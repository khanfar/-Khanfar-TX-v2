import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import paramiko
import json
from pathlib import Path
import os
import atexit
import threading
import time

class RpitxRemoteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Khanfar TX v2")
        
        # Default settings
        self.settings = {
            "host": "192.168.0.197",
            "port": 22,
            "username": "mwk",
            "password": "",
            "rpitx_path": "/home/mwk/rpitx",
            "frequency": 434.0,
            "chirp_bandwidth": 60000,
            "chirp_speed": 10,
            "saved_presets": []
        }
        
        self.load_settings()
        self.setup_gui()
        self.ssh = None
        self.current_process = None
        self.is_transmitting = False
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_settings(self):
        try:
            with open('rpitx_settings.json', 'r') as f:
                self.settings.update(json.load(f))
        except FileNotFoundError:
            self.save_settings()
            
    def save_settings(self):
        with open('rpitx_settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
            
    def setup_gui(self):
        # Connection Frame
        conn_frame = ttk.LabelFrame(self.root, text="Connection Settings", padding=10)
        conn_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(conn_frame, text="Host:").grid(row=0, column=0, sticky="w")
        self.host_entry = ttk.Entry(conn_frame)
        self.host_entry.insert(0, self.settings["host"])
        self.host_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(conn_frame, text="Username:").grid(row=1, column=0, sticky="w")
        self.user_entry = ttk.Entry(conn_frame)
        self.user_entry.insert(0, self.settings["username"])
        self.user_entry.grid(row=1, column=1, padx=5)
        
        ttk.Label(conn_frame, text="Password:").grid(row=2, column=0, sticky="w")
        self.pass_entry = ttk.Entry(conn_frame, show="*")
        self.pass_entry.insert(0, self.settings["password"])
        self.pass_entry.grid(row=2, column=1, padx=5)

        ttk.Label(conn_frame, text="Rpitx Path:").grid(row=3, column=0, sticky="w")
        self.path_entry = ttk.Entry(conn_frame)
        self.path_entry.insert(0, self.settings["rpitx_path"])
        self.path_entry.grid(row=3, column=1, padx=5)
        
        # Reset Path Button
        self.reset_path_btn = ttk.Button(conn_frame, text="Reset Path", command=self.reset_path)
        self.reset_path_btn.grid(row=3, column=2, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_ssh)
        self.connect_btn.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Frequency Frame
        freq_frame = ttk.LabelFrame(self.root, text="Frequency Settings", padding=10)
        freq_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(freq_frame, text="Frequency (MHz):").grid(row=0, column=0, sticky="w")
        self.freq_entry = ttk.Entry(freq_frame)
        self.freq_entry.insert(0, str(self.settings["frequency"]))
        self.freq_entry.grid(row=0, column=1, padx=5)
        
        # Chirp Settings Frame
        self.chirp_frame = ttk.LabelFrame(self.root, text="Chirp Settings", padding=10)
        self.chirp_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew", rowspan=2)
        
        ttk.Label(self.chirp_frame, text="Bandwidth (Hz):").grid(row=0, column=0, sticky="w")
        self.bandwidth_var = tk.StringVar(value=str(self.settings["chirp_bandwidth"]))
        self.bandwidth_spinbox = ttk.Spinbox(
            self.chirp_frame, 
            from_=1000, 
            to=10000000,
            increment=1000,
            textvariable=self.bandwidth_var,
            width=10
        )
        self.bandwidth_spinbox.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.chirp_frame, text="Speed (s):").grid(row=1, column=0, sticky="w")
        self.speed_var = tk.StringVar(value=str(self.settings["chirp_speed"]))
        self.speed_spinbox = ttk.Spinbox(
            self.chirp_frame, 
            from_=1, 
            to=60,
            increment=1,
            textvariable=self.speed_var,
            width=10
        )
        self.speed_spinbox.grid(row=1, column=1, padx=5, pady=2)
        
        # Add buttons for quick adjustments
        ttk.Button(self.chirp_frame, text="↑", width=2, 
                  command=lambda: self.adjust_bandwidth(1000)).grid(row=0, column=2)
        ttk.Button(self.chirp_frame, text="↓", width=2, 
                  command=lambda: self.adjust_bandwidth(-1000)).grid(row=0, column=3)
        
        ttk.Button(self.chirp_frame, text="↑", width=2, 
                  command=lambda: self.adjust_speed(1)).grid(row=1, column=2)
        ttk.Button(self.chirp_frame, text="↓", width=2, 
                  command=lambda: self.adjust_speed(-1)).grid(row=1, column=3)
            
        # Preset Controls
        preset_frame = ttk.Frame(self.chirp_frame)
        preset_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(preset_frame, text="Save Current Settings", 
                  command=self.save_current_settings).grid(row=0, column=0, padx=5)
        
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var)
        self.preset_combo.grid(row=0, column=1, padx=5)
        self.update_preset_list()
        
        ttk.Button(preset_frame, text="Load", 
                  command=self.load_preset).grid(row=0, column=2, padx=5)
        ttk.Button(preset_frame, text="Delete", 
                  command=self.delete_preset).grid(row=0, column=3, padx=5)
        
        # Transmission Modes Frame
        modes_frame = ttk.LabelFrame(self.root, text="Transmission Modes", padding=10)
        modes_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        modes = [
            ("Tune - Carrier Signal", self.run_tune),
            ("Chirp - Moving Carrier", self.run_chirp),
            ("Spectrum - JPG Painting", self.run_spectrum),
            ("FM RDS - Broadcast", self.run_fmrds),
            ("NFM - Narrow FM", self.run_nfm),
            ("SSB - Upper Sideband", self.run_ssb),
            ("AM - Amplitude Mod", self.run_am),
            ("FreeDV - Digital Voice", self.run_freedv),
            ("SSTV - Slow Scan TV", self.run_sstv),
            ("POCSAG - Pager", self.run_pocsag),
            ("Opera - Morse", self.run_opera),
            ("RTTY - Teletype", self.run_rtty)
        ]
        
        for i, (text, command) in enumerate(modes):
            btn = ttk.Button(modes_frame, text=text, command=command)
            btn.grid(row=i//2, column=i%2, padx=5, pady=2, sticky="ew")
            
        # Control Buttons Frame
        control_frame = ttk.Frame(self.root)
        control_frame.grid(row=3, column=0, pady=10)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Transmission", command=self.stop_transmission)
        self.stop_btn.grid(row=0, column=0, padx=5)
        
        self.force_stop_btn = ttk.Button(control_frame, text="Force Kill All", command=self.force_kill_all)
        self.force_stop_btn.grid(row=0, column=1, padx=5)
        
        # Status Label
        self.status_label = ttk.Label(control_frame, text="Status: Idle")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Update status periodically
        self.root.after(1000, self.update_status)

    def reset_path(self):
        default_path = f"/home/{self.user_entry.get()}/rpitx"
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, default_path)
        
    def connect_ssh(self):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.host_entry.get(),
                username=self.user_entry.get(),
                password=self.pass_entry.get()
            )
            messagebox.showinfo("Success", "Connected to Raspberry Pi")
            
            # Save settings
            self.settings.update({
                "host": self.host_entry.get(),
                "username": self.user_entry.get(),
                "password": self.pass_entry.get(),
                "rpitx_path": self.path_entry.get()
            })
            self.save_settings()
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.ssh = None
            
    def update_status(self):
        """Update status label periodically"""
        if self.is_transmitting:
            self.status_label.config(text="Status: Transmitting")
        else:
            self.status_label.config(text="Status: Idle")
        self.root.after(1000, self.update_status)

    def execute_command(self, command):
        if not self.ssh:
            messagebox.showerror("Error", "Not connected to Raspberry Pi")
            return
            
        try:
            freq_mhz = float(self.freq_entry.get())
            freq_hz = int(freq_mhz * 1e6)
            
            # First verify rpitx directory exists
            stdin, stdout, stderr = self.ssh.exec_command(f'test -d {self.settings["rpitx_path"]} && echo "EXISTS"')
            if not stdout.read().decode().strip() == "EXISTS":
                messagebox.showerror("Error", f"rpitx directory not found at {self.settings['rpitx_path']}")
                return
                
            # Execute the command with full path
            full_command = f'cd {self.settings["rpitx_path"]} && sudo ./{command.format(freq_hz=freq_hz)}'
            print(f"Executing: {full_command}")  # Debug output
            
            # Run command in background thread
            def run_command():
                try:
                    self.is_transmitting = True
                    self.current_process = self.ssh.get_transport().open_session()
                    self.current_process.exec_command(full_command)
                    # Wait for process to complete
                    while not self.current_process.exit_status_ready() and self.is_transmitting:
                        time.sleep(0.1)
                    self.is_transmitting = False
                except Exception as e:
                    print(f"Command error: {str(e)}")
                    self.is_transmitting = False
            
            # Start command in separate thread
            thread = threading.Thread(target=run_command, daemon=True)
            thread.start()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid frequency value")
        except Exception as e:
            messagebox.showerror("Error", f"Command execution failed: {str(e)}")
            self.is_transmitting = False

    def upload_file(self, local_path, remote_filename):
        """Upload file with proper permissions"""
        if not self.ssh:
            return None
            
        try:
            # Create temp directory if it doesn't exist
            temp_dir = f"/home/{self.settings['username']}/rpitx/temp"
            
            # Execute commands and wait for them to complete
            stdin, stdout, stderr = self.ssh.exec_command(f"sudo mkdir -p {temp_dir}")
            stdout.channel.recv_exit_status()
            
            stdin, stdout, stderr = self.ssh.exec_command(f"sudo chown -R {self.settings['username']}:{self.settings['username']} {temp_dir}")
            stdout.channel.recv_exit_status()
            
            stdin, stdout, stderr = self.ssh.exec_command(f"sudo chmod -R 755 {temp_dir}")
            stdout.channel.recv_exit_status()
            
            remote_path = f"{temp_dir}/{remote_filename}"
            
            # Upload file
            sftp = self.ssh.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            
            # Set permissions on uploaded file
            stdin, stdout, stderr = self.ssh.exec_command(f"sudo chmod 755 {remote_path}")
            stdout.channel.recv_exit_status()
            
            return remote_path
        except Exception as e:
            print(f"Upload error: {str(e)}")  # Debug print
            messagebox.showerror("Upload Error", f"Failed to upload file: {str(e)}")
            return None

    def force_stop_transmission(self):
        """Most aggressive way to stop transmission"""
        if not self.ssh:
            return
            
        try:
            # Emergency stop sequence
            emergency_commands = [
                # First stop DMA operations
                "sudo killall -9 rpitx pichirp tune",
                # Force stop all possible processes
                "sudo pkill -f -9 rpitx",
                "sudo pkill -f -9 pichirp",
                "sudo pkill -f -9 tune",
                # Kill all test scripts
                "sudo pkill -f -9 'test.*\.sh'",
                # Reset GPIO and DMA
                "sudo gpio -g write 4 0",
                "sudo gpio -g mode 4 in",
                # Stop any remaining processes
                "sudo killall -9 rpitx pichirp tune spectrumpaint pifmrds sendiq pocsag piopera freedv pisstv pirtty",
                # Clean up DMA
                "sudo rmmod rpitx_mod 2>/dev/null || true",
                # Final GPIO cleanup
                "echo 4 > /sys/class/gpio/unexport 2>/dev/null || true",
                # Reset PWM
                "sudo killall pi-blaster 2>/dev/null || true"
            ]
            
            for cmd in emergency_commands:
                try:
                    stdin, stdout, stderr = self.ssh.exec_command(cmd)
                    stdout.channel.recv_exit_status()
                except:
                    continue
                    
            time.sleep(1)  # Wait for cleanup
            
            # Verify transmission has stopped
            verify_commands = [
                "pgrep -f 'rpitx|pichirp|tune'",
                "gpio -g read 4"
            ]
            
            all_stopped = True
            for cmd in verify_commands:
                stdin, stdout, stderr = self.ssh.exec_command(cmd)
                if stdout.read():
                    all_stopped = False
                    break
            
            if all_stopped:
                messagebox.showinfo("Success", "Transmission fully stopped")
            else:
                messagebox.showwarning("Warning", "Some processes might still be running")
                
        except Exception as e:
            messagebox.showerror("Error", f"Emergency stop failed: {str(e)}")

    def stop_transmission(self):
        if self.ssh:
            self.is_transmitting = False
            if self.current_process:
                try:
                    self.current_process.close()
                except:
                    pass
            
            # Try normal stop first, then force stop
            try:
                self.force_stop_transmission()
            except:
                self.force_kill_all()

    def force_kill_all(self):
        if not self.ssh:
            if not self.connect_ssh():
                return
                
        self.is_transmitting = False
        if self.current_process:
            try:
                self.current_process.close()
            except:
                pass
        
        # Call emergency stop procedure
        self.force_stop_transmission()

    def cleanup(self):
        """Cleanup function to ensure all processes are stopped"""
        if self.ssh:
            try:
                self.force_stop_transmission()
                self.ssh.close()
            except:
                pass

    def on_closing(self):
        """Handle window closing event"""
        try:
            if messagebox.askokcancel("Quit", "Do you want to quit? This will stop all transmissions."):
                self.cleanup()
                self.root.destroy()
        except:
            self.root.destroy()

    def adjust_bandwidth(self, delta):
        try:
            current = int(self.bandwidth_var.get())
            new_value = max(1000, min(10000000, current + delta))
            self.bandwidth_var.set(str(new_value))
        except ValueError:
            self.bandwidth_var.set("60000")
            
    def adjust_speed(self, delta):
        try:
            current = int(self.speed_var.get())
            new_value = max(1, min(60, current + delta))
            self.speed_var.set(str(new_value))
        except ValueError:
            self.speed_var.set("10")

    def save_current_settings(self):
        try:
            name = simpledialog.askstring("Save Settings", "Enter name for these settings:")
            if not name:
                return
                
            # Get current settings
            preset = {
                "name": name,
                "frequency": float(self.freq_entry.get()),
                "chirp_bandwidth": int(self.bandwidth_var.get()),
                "chirp_speed": int(self.speed_var.get())
            }
            
            # Add to saved presets
            self.settings["saved_presets"] = [p for p in self.settings["saved_presets"] if p["name"] != name]
            self.settings["saved_presets"].append(preset)
            self.save_settings()
            
            # Update combo box
            self.update_preset_list()
            self.preset_var.set(name)
            
            messagebox.showinfo("Success", f"Settings saved as '{name}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            
    def update_preset_list(self):
        presets = [p["name"] for p in self.settings["saved_presets"]]
        self.preset_combo["values"] = presets
        
    def load_preset(self):
        try:
            name = self.preset_var.get()
            if not name:
                return
                
            # Find preset
            preset = next((p for p in self.settings["saved_presets"] if p["name"] == name), None)
            if not preset:
                return
                
            # Apply settings
            self.freq_entry.delete(0, tk.END)
            self.freq_entry.insert(0, str(preset["frequency"]))
            
            self.bandwidth_var.set(str(preset["chirp_bandwidth"]))
            self.speed_var.set(str(preset["chirp_speed"]))
            
            messagebox.showinfo("Success", f"Loaded settings '{name}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {str(e)}")
            
    def delete_preset(self):
        try:
            name = self.preset_var.get()
            if not name:
                return
                
            if messagebox.askyesno("Confirm Delete", f"Delete settings '{name}'?"):
                # Remove preset
                self.settings["saved_presets"] = [p for p in self.settings["saved_presets"] if p["name"] != name]
                self.save_settings()
                
                # Update combo box
                self.update_preset_list()
                self.preset_var.set("")
                
                messagebox.showinfo("Success", f"Deleted settings '{name}'")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete settings: {str(e)}")

    # Transmission mode implementations
    def run_tune(self):
        self.execute_command("./testvfo.sh {freq_hz}")
        
    def run_chirp(self):
        try:
            freq_hz = int(float(self.freq_entry.get()) * 1e6)
            bandwidth = int(self.bandwidth_var.get())
            speed = int(self.speed_var.get())
            
            # Use original pichirp command with our parameters
            command = f"./pichirp {freq_hz} {bandwidth} {speed}"
            self.execute_command(command)
        except ValueError as e:
            messagebox.showerror("Error", "Invalid frequency, bandwidth, or speed value")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start chirp: {str(e)}")
            
    def run_spectrum(self):
        file_path = filedialog.askopenfilename(filetypes=[("JPEG files", "*.jpg")])
        if file_path:
            remote_path = self.upload_file(file_path, "temp.jpg")
            if remote_path:
                self.execute_command(f"./testspectrum.sh {{freq_hz}} {remote_path}")
            
    def run_fmrds(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file_path:
            remote_path = self.upload_file(file_path, "temp.wav")
            if remote_path:
                self.execute_command(f"./testfmrds.sh {{freq_hz}} {remote_path}")
            
    def run_nfm(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file_path:
            remote_path = self.upload_file(file_path, "temp.wav")
            if remote_path:
                self.execute_command(f"./testnfm.sh {{freq_hz}} {remote_path}")
            
    def run_ssb(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file_path:
            remote_path = self.upload_file(file_path, "temp.wav")
            if remote_path:
                self.execute_command(f"./testssb.sh {{freq_hz}} {remote_path}")
            
    def run_am(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file_path:
            remote_path = self.upload_file(file_path, "temp.wav")
            if remote_path:
                self.execute_command(f"./testam.sh {{freq_hz}} {remote_path}")
            
    def run_freedv(self):
        file_path = filedialog.askopenfilename(filetypes=[("RF files", "*.rf")])
        if file_path:
            remote_path = self.upload_file(file_path, "temp.rf")
            if remote_path:
                self.execute_command(f"./testfreedv.sh {{freq_hz}} {remote_path}")
            
    def run_sstv(self):
        file_path = filedialog.askopenfilename(filetypes=[("JPEG files", "*.jpg")])
        if file_path:
            remote_path = self.upload_file(file_path, "temp.jpg")
            if remote_path:
                self.execute_command(f"./testsstv.sh {{freq_hz}} {remote_path}")
            
    def run_pocsag(self):
        try:
            # Get message from user
            message = simpledialog.askstring("POCSAG Message", "Enter message:")
            if not message:
                return
                
            # Sanitize message to prevent command injection
            message = message.replace("'", "").replace('"', "").replace(";", "")
            
            # Get frequency in Hz
            freq_hz = int(float(self.freq_entry.get()) * 1e6)
            
            # Create temp file for message
            remote_msg_path = f"/home/{self.settings['username']}/rpitx/temp/pocsag_msg.txt"
            
            # Write message to remote file
            stdin, stdout, stderr = self.ssh.exec_command(f"echo '{message}' > {remote_msg_path}")
            stdout.channel.recv_exit_status()
            
            # Run POCSAG with proper parameters
            command = f"cat {remote_msg_path} | ./pocsag -f {freq_hz}"
            self.execute_command(command)
            
        except ValueError as e:
            messagebox.showerror("Error", "Invalid frequency value")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send POCSAG message: {str(e)}")
            
    def run_opera(self):
        callsign = simpledialog.askstring("Opera Callsign", "Enter callsign:")
        if callsign:
            self.execute_command(f"./testopera.sh {{freq_hz}} '{callsign}'")
            
    def run_rtty(self):
        message = simpledialog.askstring("RTTY Message", "Enter message:")
        if message:
            self.execute_command(f"./testrtty.sh {{freq_hz}} '{message}'")

if __name__ == "__main__":
    root = tk.Tk()
    app = RpitxRemoteGUI(root)
    root.mainloop()
