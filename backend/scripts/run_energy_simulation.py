"""
RippleStorage 工商业储能调度仿真脚本
替代 OASIS 双平台并行模拟，输出兼容的 actions.jsonl
平台映射: twitter->peak_shaving, reddit->demand_response
"""
import sys, os
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONUTF8', '1')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    import builtins
    _orig_open = builtins.open
    def _utf8_open(f, m='r', b=-1, e=None, er=None, n=None, c=True, o=None):
        if e is None and 'b' not in m:
            e = 'utf-8'
        return _orig_open(f, m, b, e, er, n, c, o)
    builtins.open = _utf8_open

import argparse, json, time, random
from datetime import datetime
from typing import Dict, Any, List, Optional

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_scripts_dir, '..'))
_project_root = os.path.abspath(os.path.join(_backend_dir, '..'))
sys.path.insert(0, _scripts_dir)
sys.path.insert(0, _backend_dir)
try:
    from dotenv import load_dotenv
    _env = os.path.join(_project_root, '.env')
    if os.path.exists(_env):
        load_dotenv(_env)
except Exception:
    pass

IPC_COMMANDS_DIR = "ipc_commands"
IPC_RESPONSES_DIR = "ipc_responses"
ENV_STATUS_FILE = "env_status.json"

class CommandType:
    INTERVIEW = "interview"
    BATCH_INTERVIEW = "batch_interview"
    CLOSE_ENV = "close_env"

class EnergyIPCHandler:
    PROFILES = {
        0: {"name": "EMS-主控", "role": "能量管理系统", "desc": "负责全局调度策略与收益优化"},
        1: {"name": "BMS-电池", "role": "电池管理系统", "desc": "监控电芯状态、SOC、温度与安全边界"},
        2: {"name": "PCS-变流", "role": "储能变流器", "desc": "控制交直流转换与功率响应速度"},
        3: {"name": "Load-负荷", "role": "负荷预测Agent", "desc": "基于历史数据预测未来用电需求"},
    }
    def __init__(self, sim_dir: str, state: Dict):
        self.sim_dir = sim_dir
        self.state = state
        self.cmd_dir = os.path.join(sim_dir, IPC_COMMANDS_DIR)
        self.res_dir = os.path.join(sim_dir, IPC_RESPONSES_DIR)
        self.status_file = os.path.join(sim_dir, ENV_STATUS_FILE)
        os.makedirs(self.cmd_dir, exist_ok=True)
        os.makedirs(self.res_dir, exist_ok=True)
    def update_status(self, status: str):
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump({"status": status, "energy_available": True, "timestamp": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    def poll_command(self) -> Optional[Dict]:
        if not os.path.exists(self.cmd_dir):
            return None
        files = [(os.path.join(self.cmd_dir, n), os.path.getmtime(os.path.join(self.cmd_dir, n))) for n in os.listdir(self.cmd_dir) if n.endswith('.json')]
        files.sort(key=lambda x: x[1])
        for fp, _ in files:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                continue
        return None
    def send_response(self, cid, status, result=None, error=None):
        with open(os.path.join(self.res_dir, f"{cid}.json"), 'w', encoding='utf-8') as f:
            json.dump({"command_id": cid, "status": status, "result": result, "error": error, "timestamp": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        try:
            os.remove(os.path.join(self.cmd_dir, f"{cid}.json"))
        except OSError:
            pass
    def _resp(self, aid, prompt):
        p = self.PROFILES.get(aid, {"name": f"Agent-{aid}", "role": "系统组件", "desc": "参与储能协同控制"})
        s = self.state
        text = prompt.lower()
        if "收益" in text or "revenue" in text or "profit" in text:
            return f"[{p['name']}] 当前累计收益约 ¥{s['daily_revenue']:,.0f}，SOC 维持在 {s['soc']*100:.0f}%。"
        if "soc" in text or "电量" in text or "状态" in text:
            return f"[{p['name']}] 当前 SOC 为 {s['soc']*100:.1f}%，处于{'放电区间' if s['soc'] > 0.5 else '充电区间'}，运行正常。"
        if "削峰" in text or "peak" in text or "需量" in text:
            return f"[{p['name']}] 本日最大削峰功率 {s['peak_shaved_kw']} kW，有效降低了变压器需量电费。"
        return f"[{p['name']}] {p['desc']}。当前模拟运行至第 {s['current_hour']} 时，系统状态平稳。"
    def handle_interview(self, cid, aid, prompt):
        self.send_response(cid, "completed", {"agent_id": aid, "response": self._resp(aid, prompt), "timestamp": datetime.now().isoformat()})
        return True
    def handle_batch(self, cid, interviews):
        res = {}
        for iv in interviews:
            aid = iv.get("agent_id", 0)
            res[str(aid)] = {"agent_id": aid, "response": self._resp(aid, iv.get("prompt", "")), "timestamp": datetime.now().isoformat()}
        self.send_response(cid, "completed", {"interviews_count": len(res), "results": res})
        return True
    def process_commands(self) -> bool:
        cmd = self.poll_command()
        if not cmd:
            return True
        cid, ctype, args = cmd.get("command_id"), cmd.get("command_type"), cmd.get("args", {})
        if ctype == CommandType.INTERVIEW:
            self.handle_interview(cid, args.get("agent_id", 0), args.get("prompt", ""))
        elif ctype == CommandType.BATCH_INTERVIEW:
            self.handle_batch(cid, args.get("interviews", []))
        elif ctype == CommandType.CLOSE_ENV:
            self.send_response(cid, "completed", {"message": "环境即将关闭"})
            return False
        return True

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def price_at(hour, tariff):
    peak = set(tariff.get("peak_hours", [9,10,11,12,13,14,19,20,21]))
    valley = set(tariff.get("valley_hours", [0,1,2,3,4,5,6,7]))
    if hour in peak:
        return tariff.get("peak_price", 1.2)
    if hour in valley:
        return tariff.get("valley_price", 0.3)
    return tariff.get("flat_price", 0.8)

def load_at(hour, cfg):
    base, peak = cfg.get("base_load_kw", 500), cfg.get("peak_load_kw", 2000)
    curve = [0.45,0.40,0.38,0.36,0.38,0.50,0.70,0.85,0.95,1.00,0.98,0.95,0.90,0.88,0.92,0.95,0.85,0.75,0.70,0.65,0.60,0.55,0.50,0.47]
    return (base + (peak - base) * curve[hour % 24]) * (1 + random.uniform(-0.02, 0.02))

def decide(hour, soc, price, load, battery, platform):
    cap = battery.get("capacity_kwh", 2000)
    max_c = battery.get("max_charge_kw", 1000)
    max_d = battery.get("max_discharge_kw", 1000)
    eff = battery.get("efficiency", 0.92)
    min_soc = battery.get("min_soc", 0.1)
    max_soc = battery.get("max_soc", 0.95)
    if platform == "twitter":
        if price <= 0.4 and soc < max_soc:
            return {"type": "CHARGE", "power_kw": round(min(max_c, (max_soc - soc) * cap / eff), 1), "reason": "低谷充电"}
        if price >= 0.9 and soc > min_soc:
            return {"type": "DISCHARGE", "power_kw": round(min(max_d, (soc - min_soc) * cap * eff), 1), "reason": "高峰放电"}
        return {"type": "IDLE", "power_kw": 0, "reason": "保持待机"}
    else:
        threshold = load * 0.85
        if load > threshold and soc > min_soc:
            return {"type": "PEAK_CUT", "power_kw": round(min(max_d, load - threshold, (soc - min_soc) * cap * eff), 1), "reason": "削峰响应"}
        if load < threshold * 0.6 and soc < max_soc:
            return {"type": "VALLEY_FILL", "power_kw": round(min(max_c, (max_soc - soc) * cap / eff), 1), "reason": "填谷充电"}
        return {"type": "IDLE", "power_kw": 0, "reason": "负荷平稳"}

def run_simulation(config_path, max_rounds=None, no_wait=False):
    config = load_config(config_path)
    sim_dir = os.path.dirname(os.path.abspath(config_path))
    tc = config.get("time_config", {})
    total_hours = tc.get("total_simulation_hours", 24)
    minutes = tc.get("minutes_per_round", 60)
    rounds = int(total_hours * 60 / max(minutes, 1))
    if max_rounds:
        rounds = min(rounds, max_rounds)
    battery = config.get("battery_config", {})
    tariff = config.get("tariff_config", {})
    load_cfg = config.get("load_config", {})
    cap = battery.get("capacity_kwh", 2000)
    eff = battery.get("efficiency", 0.92)
    soc = battery.get("initial_soc", 0.2)
    state = {"soc": soc, "current_hour": 0, "daily_revenue": 0.0, "peak_shaved_kw": 0}
    os.makedirs(os.path.join(sim_dir, "twitter"), exist_ok=True)
    os.makedirs(os.path.join(sim_dir, "reddit"), exist_ok=True)
    tw_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
    rd_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
    ipc = EnergyIPCHandler(sim_dir, state)
    ipc.update_status("running")
    print(f"启动储能仿真: {rounds} 轮")
    with open(tw_log, 'w', encoding='utf-8') as ft, open(rd_log, 'w', encoding='utf-8') as fr:
        for r in range(1, rounds + 1):
            hour = (r - 1) % 24
            state["current_hour"] = hour
            p = price_at(hour, tariff)
            l = load_at(hour, load_cfg)
            for f in (ft, fr):
                f.write(json.dumps({"round": r, "timestamp": datetime.now().isoformat(), "event_type": "round_start", "simulated_hour": hour}, ensure_ascii=False) + "\n")
                f.flush()
            tw = decide(hour, soc, p, l, battery, "twitter")
            rd = decide(hour, soc, p, l, battery, "reddit")
            for f, action, plat in ((ft, tw, "twitter"), (fr, rd, "reddit")):
                entry = {
                    "round": r, "timestamp": datetime.now().isoformat(),
                    "agent_id": 0, "agent_name": "储能主控" if plat == "twitter" else "需量管理",
                    "action_type": action["type"],
                    "action_args": {"power_kw": action["power_kw"], "reason": action["reason"], "soc_before": round(soc, 3), "price": round(p, 2), "load": round(l, 1)},
                    "success": True
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f.flush()
            power = tw["power_kw"]
            if tw["type"] == "CHARGE":
                soc = min(soc + power * (minutes / 60) / cap * eff, battery.get("max_soc", 0.95))
            elif tw["type"] in ("DISCHARGE", "PEAK_CUT"):
                soc = max(soc - power * (minutes / 60) / cap / eff, battery.get("min_soc", 0.1))
            state["soc"] = soc
            if tw["type"] == "DISCHARGE":
                state["daily_revenue"] += power * (minutes / 60) * p * 0.85
            elif tw["type"] == "CHARGE":
                state["daily_revenue"] -= power * (minutes / 60) * p
            if rd["type"] == "PEAK_CUT":
                state["peak_shaved_kw"] = max(state["peak_shaved_kw"], int(rd["power_kw"]))
            for f in (ft, fr):
                f.write(json.dumps({"round": r, "timestamp": datetime.now().isoformat(), "event_type": "round_end", "simulated_hours": hour + 1, "actions_count": 1}, ensure_ascii=False) + "\n")
                f.flush()
            time.sleep(0.2)
            while True:
                if not ipc.process_commands():
                    print("收到关闭命令，提前结束")
                    return
                if not ipc.poll_command():
                    break
        end = datetime.now().isoformat()
        for f, plat in ((ft, "twitter"), (fr, "reddit")):
            f.write(json.dumps({"timestamp": end, "event_type": "simulation_end", "platform": plat, "total_rounds": rounds, "total_actions": rounds}, ensure_ascii=False) + "\n")
    print(f"仿真完成: 收益=¥{state['daily_revenue']:,.0f}, 削峰={state['peak_shaved_kw']}kW")
    if no_wait:
        ipc.update_status("stopped")
        return
    print("\n进入等待命令模式...")
    ipc.update_status("waiting")
    while True:
        if not ipc.process_commands():
            break
        time.sleep(1)
    ipc.update_status("stopped")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--max-rounds", type=int, default=None)
    parser.add_argument("--no-wait", action="store_true")
    args = parser.parse_args()
    run_simulation(args.config, max_rounds=args.max_rounds, no_wait=args.no_wait)

if __name__ == "__main__":
    main()
