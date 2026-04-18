import tkinter as tk
from tkinter import ttk, messagebox
import requests
import random
import threading

class ScreenTestTool:
    def __init__(self, root):
        self.root = root
        self.root.title("硬件打屏测试工具")
        self.root.geometry("550x600")
        
        # --- 变量定义 ---
        self.ip_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="16869")
        
        self.device_list = [] # 存储 (text, value)
        self.device_var = tk.StringVar()
        
        self.gray_var = tk.IntVar(value=255)
        self.style_var = tk.StringVar(value="红色") # 默认红色
        
        self.jump_space_var = tk.IntVar(value=1)
        self.grid_size_var = tk.IntVar(value=32)
        
        self.start_x_var = tk.IntVar(value=0)
        self.start_y_var = tk.IntVar(value=0)
        self.width_var = tk.IntVar(value=512)
        self.height_var = tk.IntVar(value=512)
        self.window_no_var = tk.IntVar(value=1)

        self._create_ui()
        self._bind_events()
        
        # 初始化加载设备
        self.load_devices()

    def _create_ui(self):
        # --- 1. 连接设置 ---
        frame_conn = tk.LabelFrame(self.root, text="连接设置", padx=10, pady=10)
        frame_conn.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_conn, text="IP地址:").grid(row=0, column=0, sticky="e")
        tk.Entry(frame_conn, textvariable=self.ip_var, width=15).grid(row=0, column=1, padx=5, sticky="w")

        tk.Label(frame_conn, text="端口:").grid(row=0, column=2, sticky="e")
        tk.Entry(frame_conn, textvariable=self.port_var, width=10).grid(row=0, column=3, padx=5, sticky="w")

        tk.Label(frame_conn, text="设备列表:").grid(row=1, column=0, sticky="e", pady=(10,0))
        self.combo_device = ttk.Combobox(frame_conn, textvariable=self.device_var, state="readonly", width=40)
        self.combo_device.grid(row=1, column=1, columnspan=3, padx=5, pady=(10,0), sticky="w")

        # --- 2. 参数设置 ---
        frame_params = tk.LabelFrame(self.root, text="打屏参数", padx=10, pady=10)
        frame_params.pack(fill="x", padx=10, pady=5)

        # 灰阶
        tk.Label(frame_params, text="灰阶 (0-255):").grid(row=0, column=0, sticky="e")
        tk.Spinbox(frame_params, from_=0, to=255, textvariable=self.gray_var, width=10).grid(row=0, column=1, sticky="w")

        # 样式 (Radio)
        tk.Label(frame_params, text="打屏样式:").grid(row=1, column=0, sticky="e", pady=5)
        styles = ["红色", "绿色", "蓝色", "白色", "棋盘格"]
        for i, style in enumerate(styles):
            rb = tk.Radiobutton(frame_params, text=style, variable=self.style_var, value=style)
            rb.grid(row=1, column=i+1, sticky="w", padx=5, pady=5)
        
        # 动态控件容器
        self.frame_extra = tk.Frame(frame_params)
        self.frame_extra.grid(row=2, column=0, columnspan=6, sticky="w")
        
        # 跳点间距 (默认显示)
        self.lbl_jump = tk.Label(self.frame_extra, text="跳点间距 (1-10):")
        self.lbl_jump.pack(side="left")
        self.spb_jump = tk.Spinbox(self.frame_extra, from_=1, to=10, textvariable=self.jump_space_var, width=8)
        self.spb_jump.pack(side="left", padx=5)

        # 棋盘格大小 (默认隐藏)
        self.lbl_grid = tk.Label(self.frame_extra, text="棋盘格大小 (1-63):")
        self.spb_grid = tk.Spinbox(self.frame_extra, from_=1, to=512, textvariable=self.grid_size_var, width=8)

        # --- 3. 坐标与窗口 ---
        frame_coord = tk.LabelFrame(self.root, text="坐标与窗口", padx=10, pady=10)
        frame_coord.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_coord, text="起始X:").grid(row=0, column=0, sticky="e")
        tk.Spinbox(frame_coord, from_=0, to=2000, textvariable=self.start_x_var, width=8).grid(row=0, column=1, sticky="w")

        tk.Label(frame_coord, text="起始Y:").grid(row=0, column=2, sticky="e", padx=(10,0))
        tk.Spinbox(frame_coord, from_=0, to=2000, textvariable=self.start_y_var, width=8).grid(row=0, column=3, sticky="w")

        tk.Label(frame_coord, text="宽度:").grid(row=1, column=0, sticky="e", pady=5)
        tk.Spinbox(frame_coord, from_=1, to=2000, textvariable=self.width_var, width=8).grid(row=1, column=1, sticky="w")

        tk.Label(frame_coord, text="高度:").grid(row=1, column=2, sticky="e", padx=(10,0), pady=5)
        tk.Spinbox(frame_coord, from_=1, to=2000, textvariable=self.height_var, width=8).grid(row=1, column=3, sticky="w")

        # 终止坐标显示
        self.end_coord_label = tk.Label(frame_coord, text="终止点: 63 , 63", fg="blue", anchor="w")
        self.end_coord_label.grid(row=2, column=0, columnspan=4, pady=5, sticky="we")

        tk.Label(frame_coord, text="窗口号(1-4):").grid(row=3, column=0, sticky="e")
        tk.Spinbox(frame_coord, from_=1, to=4, textvariable=self.window_no_var, width=8).grid(row=3, column=1, sticky="w")

        # --- 4. 按钮 ---
        frame_btn = tk.Frame(self.root, pady=15)
        frame_btn.pack(fill="x", padx=20)

        tk.Button(frame_btn, text="刷新列表", command=self.load_devices, height=2).pack(side="left", padx=10, expand=True, fill="x")
        tk.Button(frame_btn, text="开始打屏", command=self.action_start, bg="#4CAF50", fg="white", font=("微软雅黑", 10, "bold"), height=2).pack(side="left", padx=10, expand=True, fill="x")
        tk.Button(frame_btn, text="关闭打屏", command=self.action_stop, bg="#f44336", fg="white", font=("微软雅黑", 10, "bold"), height=2).pack(side="left", padx=10, expand=True, fill="x")

    def _bind_events(self):
        # 监听样式变化
        self.style_var.trace_add("write", self.on_style_change)
        # 监听坐标变化
        for var in [self.start_x_var, self.start_y_var, self.width_var, self.height_var]:
            var.trace_add("write", self.update_end_coord_display)
        
        # 初始化样式显示
        self.on_style_change()

    def update_end_coord_display(self, *args):
        try:
            x = self.start_x_var.get()
            y = self.start_y_var.get()
            w = self.width_var.get()
            h = self.height_var.get()
            end_x = x + w - 1
            end_y = y + h - 1
            self.end_coord_label.config(text=f"终止点计算: {end_x} , {end_y}")
        except:
            pass

    def on_style_change(self, *args):
        style = self.style_var.get()
        if style == "棋盘格":
            self.lbl_jump.pack_forget()
            self.spb_jump.pack_forget()
            self.lbl_grid.pack(side="left")
            self.spb_grid.pack(side="left", padx=5)
        else:
            self.lbl_grid.pack_forget()
            self.spb_grid.pack_forget()
            self.lbl_jump.pack(side="left")
            self.spb_jump.pack(side="left", padx=5)

    # --- 逻辑处理 ---

    def get_base_url(self):
        return f"http://{self.ip_var.get()}:{self.port_var.get()}"

    def load_devices(self):
        url = f"{self.get_base_url()}/api/unilic/device-connection"
        params = {"_t": random.random()}
        headers = {
            "content-type": "application/json",
            "operate-mode": "DEV",
            "receiver-type": "DGB"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=3)
            response.raise_for_status()
            data = response.json()
            
            # 解析数据
            devices = data if isinstance(data, list) else data.get("data", [])
            
            self.device_list = []
            combo_values = []
            
            for dev in devices:
                name = dev.get("connectName")
                dev_id = dev.get("deviceId")
                if name and dev_id:
                    display_text = f"{name}"
                    self.device_list.append((display_text, dev_id))
                    combo_values.append(display_text)
            
            self.combo_device['values'] = combo_values
            if combo_values:
                self.combo_device.current(0)
                
        except Exception as e:
            messagebox.showwarning("连接提示", f"获取设备列表失败:\n{e}")

    def get_current_device_id(self):
        display_text = self.device_var.get()
        for text, dev_id in self.device_list:
            if text == display_text:
                return dev_id
        return None

    def validate_inputs(self):
        if not self.get_current_device_id():
            messagebox.showerror("错误", "请先刷新并选择设备")
            return False
        
        try:
            # 简单验证数值范围
            gray = self.gray_var.get()
            if not (0 <= gray <= 255): raise ValueError("灰阶范围错误")
            
            if self.style_var.get() == "棋盘格":
                size = self.grid_size_var.get()
                if not (1 <= size <= 512): raise ValueError("棋盘格大小范围错误")
            else:
                space = self.jump_space_var.get()
                if not (1 <= space <= 10): raise ValueError("跳点间距范围错误")
                
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return False
            
        return True

    def build_command(self, is_close=False):
        device_id = self.get_current_device_id()
        win_no = self.window_no_var.get()
        if win_no > 4:
            win_no = 4
        x = self.start_x_var.get()
        y = self.start_y_var.get()
        w = self.width_var.get()
        h = self.height_var.get()
        gray = hex(self.gray_var.get()).replace("0x","")

        end_x = x + w - 1
        end_y = y + h - 1

        if is_close:
            # 关闭指令: {WSCT,地址位,Flag,窗口号-0}
            return f"{{WSCT,A001,0,{win_no}-0}}"

        # 打屏指令
        style = self.style_var.get()
        flag = 1
        status = 1
        border = 0

        if style == "棋盘格":
            # Type 0
            grid_size = self.grid_size_var.get()
            color1 = int(gray + gray + gray, 16)
            color2 = int("000000", 16)

            # 窗口-1-0-X-Y-EndX-EndY-C1-C2-Size-Border
            param_str = f"{win_no}-{status}-0-{x}-{y}-{end_x}-{end_y}-{color1}-{color2}-{grid_size}-{border}"
            return f"{{WSCT,A001,{flag},{param_str}}}"

        else:
            # 颜色映射
            color_map = {"红色": gray+"0000", "绿色": "00"+gray+"00", "蓝色": "0000"+gray, "白色": gray + gray + gray}
            color = color_map.get(style, gray+"0000")
            color = int(color, 16)
            jump_space = self.jump_space_var.get()
            if jump_space == 1:
                # Type 1: 纯色
                param_str = f"{win_no}-{status}-1-{x}-{y}-{end_x}-{end_y}-{color}"
            else:
                # Type 2: 跳点
                # 跳点起始坐标默认使用窗口起始坐标 X, Y
                param_str = f"{win_no}-{status}-2-{x}-{y}-{end_x}-{end_y}-{x}-{y}-{color}-{jump_space}-{border}"
            
            return f"{{WSCT,A001,{flag},{param_str}}}"

    def send_request(self, command, is_close=False):
        url = f"{self.get_base_url()}/api/unilic/debug-tool"
        params = {"_t": random.random()}
        
        device_id = self.get_current_device_id()
        headers = {
            "Content-Type": "application/json",
            "Device-Id": device_id,
            "Operate-Mode": "DEV",
            "Receiver-Type": "DGB"
        }
        
        # 假设POST body包含command字段
        payload = {"commandType": "ASCII","asciiContent": command}
        try:
            response = requests.post(url, json=payload, headers=headers, params=params, timeout=5)
            response.raise_for_status()
            res_text = response.text
            if "OK" in res_text:
                messagebox.showinfo("成功", "指令执行成功：\n发送: "  + command + "\n返回: "  + res_text)
            else:
                messagebox.showwarning("失败", "指令执行失败：\n发送: "  + command + "\n返回: " + res_text)
                
        except Exception as e:
            messagebox.showerror("通信失败", f"执行失败:\n{e}")

    def action_start(self):
        if self.validate_inputs():
            cmd = self.build_command(is_close=False)
            threading.Thread(target=self.send_request, args=(cmd, False)).start()

    def action_stop(self):
        if not self.get_current_device_id():
            messagebox.showerror("错误", "请先选择设备")
            return
            
        cmd = self.build_command(is_close=True)
        threading.Thread(target=self.send_request, args=(cmd, True)).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenTestTool(root)
    root.mainloop()