import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import requests
import base64
import json
import io
import cv2
import numpy as np
import threading
import random
from datetime import datetime
import os
import csv
import time
import winsound
import pygame 

class FireDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fire Detector App")
        self.root.geometry("1300x900")  # Increased window size
        self.root.configure(bg="#0b66c2")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors
        self.configure_styles()
        
        # Detection methods
        self.detection_methods = ["Color-Based", "Temperature Simulation", "Motion-Based", "Advanced AI"]
        self.current_method = "Color-Based"
        
        # Store detection history with file persistence
        self.detection_history = []
        self.history_counter = 1
        self.history_file = "detection_history.json"
        
        # Alarm settings
        self.alarm_enabled = True
        self.alarm_type = "Visual"  # Visual, Sound, Both
        self.alarm_sound = "Siren"  # Siren, Beep, Alert
        self.alarm_duration = 10  # seconds
        self.alarm_volume = 0.7  # 0.0 to 1.0
        
        # Alarm state
        self.alarm_active = False
        self.alarm_start_time = None
        
        # Initialize pygame for sound
        try:
            pygame.mixer.init()
            self.sound_available = True
        except:
            self.sound_available = False
            print("Sound system not available")
        
        # Load existing history
        self.load_history_from_file()
        
        # Alert settings
        self.alert_enabled = True
        self.confidence_threshold = 0.7
        
        # Create UI
        self.create_widgets()
        
    def configure_styles(self):
        # Configure styles for a more colorful UI
        self.style.configure('TFrame', background="#2c5035")
        self.style.configure('TLabel', background='#2c3e50', foreground='white')
        self.style.configure('TButton', background='#3498db', foreground='white')
        self.style.configure('Title.TLabel', font=('Arial', 18, 'bold'), foreground='#e74c3c')
        self.style.configure('Section.TLabelframe', background='#34495e', foreground='white')
        self.style.configure('Section.TLabelframe.Label', background='#34495e', foreground='#f39c12')
        
        # Button styles
        self.style.configure('Primary.TButton', background="#3010e3", foreground='white')
        self.style.configure('Success.TButton', background='#2ecc71', foreground='white')
        self.style.configure('Danger.TButton', background='#e74c3c', foreground='white')
        self.style.configure('Warning.TButton', background='#f39c12', foreground='white')
        self.style.configure('Info.TButton', background='#17a2b8', foreground='white')
        self.style.configure('Alarm.TButton', background='#ff0000', foreground='white', font=('Arial', 10, 'bold'))
        
        # Treeview styles
        self.style.configure('Treeview', background='#ecf0f1', fieldbackground='#ecf0f1', foreground='#2c3e50')
        self.style.configure('Treeview.Heading', background="#7563A4",foreground="#0d0d0d")
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔥 Fire Detection System 🔥", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Detection Settings", padding="8", style='Section.TLabelframe')
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=3)
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)
        
        ttk.Label(settings_frame, text="Detection Method:").grid(row=0, column=0, sticky=tk.W, padx=3)
        self.method_var = tk.StringVar(value=self.current_method)
        method_combo = ttk.Combobox(settings_frame, textvariable=self.method_var, values=self.detection_methods, 
                                   state="readonly", width=15)
        method_combo.grid(row=0, column=1, padx=3, sticky=(tk.W, tk.E))
        method_combo.bind('<<ComboboxSelected>>', self.on_method_change)
        
        ttk.Label(settings_frame, text="Confidence Threshold:").grid(row=0, column=2, sticky=tk.W, padx=3)
        self.threshold_var = tk.DoubleVar(value=self.confidence_threshold)
        threshold_scale = ttk.Scale(settings_frame, from_=0.1, to=1.0, variable=self.threshold_var, 
                                   orient=tk.HORIZONTAL, length=120)
        threshold_scale.grid(row=0, column=3, padx=3, sticky=(tk.W, tk.E))
        
        self.alert_var = tk.BooleanVar(value=self.alert_enabled)
        ttk.Checkbutton(settings_frame, text="Enable Alerts", variable=self.alert_var).grid(row=0, column=4, padx=10)
        
        # Alarm Settings frame - Made more compact
        alarm_frame = ttk.LabelFrame(main_frame, text="Alarm Settings", padding="8", style='Section.TLabelframe')
        alarm_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=3)
        
        # First row of alarm settings
        alarm_row1 = ttk.Frame(alarm_frame)
        alarm_row1.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(alarm_row1, text="Alarm Type:").grid(row=0, column=0, sticky=tk.W, padx=3)
        self.alarm_type_var = tk.StringVar(value=self.alarm_type)
        alarm_type_combo = ttk.Combobox(alarm_row1, textvariable=self.alarm_type_var, 
                                       values=["Visual", "Sound", "Both"], state="readonly", width=8)
        alarm_type_combo.grid(row=0, column=1, padx=3, sticky=tk.W)
        
        ttk.Label(alarm_row1, text="Sound:").grid(row=0, column=2, sticky=tk.W, padx=3)
        self.alarm_sound_var = tk.StringVar(value=self.alarm_sound)
        alarm_sound_combo = ttk.Combobox(alarm_row1, textvariable=self.alarm_sound_var, 
                                        values=["Siren", "Beep", "Alert", "Emergency"], state="readonly", width=8)
        alarm_sound_combo.grid(row=0, column=3, padx=3, sticky=tk.W)
        
        ttk.Label(alarm_row1, text="Duration (s):").grid(row=0, column=4, sticky=tk.W, padx=3)
        self.alarm_duration_var = tk.IntVar(value=self.alarm_duration)
        alarm_duration_spin = ttk.Spinbox(alarm_row1, from_=5, to=60, textvariable=self.alarm_duration_var, width=5)
        alarm_duration_spin.grid(row=0, column=5, padx=3, sticky=tk.W)
        
        # Second row of alarm settings
        alarm_row2 = ttk.Frame(alarm_frame)
        alarm_row2.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(alarm_row2, text="Volume:").grid(row=0, column=0, sticky=tk.W, padx=3)
        self.alarm_volume_var = tk.DoubleVar(value=self.alarm_volume)
        alarm_volume_scale = ttk.Scale(alarm_row2, from_=0.0, to=1.0, variable=self.alarm_volume_var, 
                                      orient=tk.HORIZONTAL, length=80)
        alarm_volume_scale.grid(row=0, column=1, padx=3, sticky=tk.W)
        
        ttk.Button(alarm_row2, text="Test Alarm", command=self.test_alarm, style='Warning.TButton').grid(row=0, column=2, padx=5)
        self.stop_alarm_button = ttk.Button(alarm_row2, text="Stop Alarm", command=self.stop_alarm, style='Danger.TButton')
        self.stop_alarm_button.grid(row=0, column=3, padx=5)
        
        # Upload section - Made more compact
        upload_frame = ttk.LabelFrame(main_frame, text="Image Upload & Capture", padding="8", style='Section.TLabelframe')
        upload_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=3)
        upload_frame.columnconfigure(1, weight=1)
        
        # File selection row
        file_row = ttk.Frame(upload_frame)
        file_row.grid(row=0, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=2)
        file_row.columnconfigure(1, weight=1)
        
        ttk.Label(file_row, text="Select Image:").grid(row=0, column=0, sticky=tk.W, padx=3)
        
        self.image_path = tk.StringVar()
        entry = ttk.Entry(file_row, textvariable=self.image_path, width=40)
        entry.grid(row=0, column=1, padx=3, sticky=(tk.W, tk.E))
        
        ttk.Button(file_row, text="Browse", command=self.browse_image, style='Primary.TButton').grid(row=0, column=2, padx=3)
        ttk.Button(file_row, text="Detect Fire", command=self.detect_fire, style='Success.TButton').grid(row=0, column=3, padx=3)
        ttk.Button(file_row, text="Batch Process", command=self.batch_process, style='Info.TButton').grid(row=0, column=4, padx=3)
        
        # Webcam section
        webcam_frame = ttk.Frame(upload_frame)
        webcam_frame.grid(row=1, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(webcam_frame, text="Start Webcam", command=self.start_webcam, style='Primary.TButton').grid(row=0, column=0, padx=3)
        ttk.Button(webcam_frame, text="Capture & Detect", command=self.capture_webcam, style='Success.TButton').grid(row=0, column=1, padx=3)
        ttk.Button(webcam_frame, text="Stop Webcam", command=self.stop_webcam, style='Danger.TButton').grid(row=0, column=2, padx=3)
        ttk.Button(webcam_frame, text="Continuous Detection", command=self.toggle_continuous_detection, style='Warning.TButton').grid(row=0, column=3, padx=3)
        
        # Image display
        display_frame = ttk.Frame(main_frame)
        display_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=8)
        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        display_frame.rowconfigure(0, weight=1)
        
        # Original image
        orig_frame = ttk.LabelFrame(display_frame, text="Original Image", padding="5", style='Section.TLabelframe')
        orig_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        orig_frame.columnconfigure(0, weight=1)
        orig_frame.rowconfigure(0, weight=1)
        
        self.original_image_label = ttk.Label(orig_frame, text="No image selected", background='#34495e', foreground='white')
        self.original_image_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Processed image
        proc_frame = ttk.LabelFrame(display_frame, text="Processed Image", padding="5", style='Section.TLabelframe')
        proc_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        proc_frame.columnconfigure(0, weight=1)
        proc_frame.rowconfigure(0, weight=1)
        
        self.processed_image_label = ttk.Label(proc_frame, text="Processing results will appear here", background='#34495e', foreground='white')
        self.processed_image_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Detection Results", padding="8", style='Section.TLabelframe')
        results_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=3)
        results_frame.columnconfigure(0, weight=1)
        
        self.result_var = tk.StringVar(value="No detection performed yet")
        result_label = ttk.Label(results_frame, textvariable=self.result_var, font=("Arial", 12), 
                                background='#34495e', foreground='white', wraplength=1000)
        result_label.grid(row=0, column=0, columnspan=2, pady=3, sticky=(tk.W, tk.E))
        
        # Statistics frame
        stats_frame = ttk.Frame(results_frame)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=3)
        
        self.stats_var = tk.StringVar(value="Total Detections: 0 | Fires Detected: 0 | Accuracy: 0%")
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var, font=("Arial", 10))
        stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # History section
        history_frame = ttk.LabelFrame(main_frame, text="Detection History", padding="8", style='Section.TLabelframe')
        history_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=3)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Create treeview for history
        columns = ("id", "image_name", "method", "has_fire", "confidence", "created_at")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=6)
        
        # Define headings
        self.history_tree.heading("id", text="ID")
        self.history_tree.heading("image_name", text="Image Name")
        self.history_tree.heading("method", text="Method")
        self.history_tree.heading("has_fire", text="Fire Detected")
        self.history_tree.heading("confidence", text="Confidence")
        self.history_tree.heading("created_at", text="Date")
        
        # Define columns
        self.history_tree.column("id", width=40, anchor='center')
        self.history_tree.column("image_name", width=120)
        self.history_tree.column("method", width=100)
        self.history_tree.column("has_fire", width=80, anchor='center')
        self.history_tree.column("confidence", width=80, anchor='center')
        self.history_tree.column("created_at", width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # History buttons frame
        history_buttons_frame = ttk.Frame(history_frame)
        history_buttons_frame.grid(row=1, column=0, columnspan=2, pady=3)
        
        ttk.Button(history_buttons_frame, text="Refresh History", command=self.load_history, 
                  style='Primary.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(history_buttons_frame, text="Clear History", command=self.clear_history, 
                  style='Danger.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(history_buttons_frame, text="Export to CSV", command=self.export_history, 
                  style='Success.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(history_buttons_frame, text="View Statistics", command=self.show_statistics, 
                  style='Info.TButton').pack(side=tk.LEFT, padx=2)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=3)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Webcam variables
        self.webcam_running = False
        self.continuous_detection = False
        self.cap = None
        
        # Alarm variables
        self.alarm_flash_count = 0
        self.alarm_sound_thread = None
        
        # Load initial history
        self.load_history()
        self.update_statistics()

    # DATA PERSISTENCE METHODS
    def load_history_from_file(self):
        """Load history from JSON file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                    if history:
                        self.detection_history = history
                        self.history_counter = max(item['id'] for item in history) + 1
        except Exception as e:
            print(f"Error loading history: {e}")

    def save_history_to_file(self):
        """Save history to JSON file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.detection_history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def save_to_history(self, image_name, has_fire, confidence):
        """Save current detection result to history"""
        history_item = {
            'id': self.history_counter,
            'image_name': image_name,
            'method': self.current_method,
            'has_fire': has_fire,
            'confidence': confidence,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.detection_history.append(history_item)
        self.history_counter += 1
        
        # Save to file
        self.save_history_to_file()
        
        # Update history display
        self.load_history()
        self.update_statistics()

    def load_history(self):
        try:
            # Clear current treeview
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # Add current detection history (reversed to show latest first)
            for item in reversed(self.detection_history):
                fire_text = "✅ Yes" if item['has_fire'] else "❌ No"
                self.history_tree.insert("", "end", values=(
                    item['id'],
                    item['image_name'],
                    item['method'],
                    fire_text,
                    f"{item['confidence']:.2%}",
                    item['created_at']
                ))
            
            history_count = len(self.detection_history)
            self.status_var.set(f"History loaded: {history_count} records")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {e}")
            self.status_var.set("History load failed")

    def clear_history(self):
        """Clear all history"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all detection history?"):
            self.detection_history = []
            self.history_counter = 1
            self.save_history_to_file()
            self.load_history()
            self.update_statistics()
            self.status_var.set("History cleared")

    def export_history(self):
        """Export history to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['ID', 'Image Name', 'Method', 'Fire Detected', 'Confidence', 'Timestamp'])
                    for item in self.detection_history:
                        writer.writerow([
                            item['id'],
                            item['image_name'],
                            item['method'],
                            'Yes' if item['has_fire'] else 'No',
                            f"{item['confidence']:.2%}",
                            item['created_at']
                        ])
                self.status_var.set(f"History exported to {filename}")
                messagebox.showinfo("Export Successful", f"History exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export history: {e}")

    def update_statistics(self):
        """Update statistics display"""
        total = len(self.detection_history)
        fires = sum(1 for item in self.detection_history if item['has_fire'])
        accuracy = fires / total * 100 if total > 0 else 0
        
        self.stats_var.set(f"Total Detections: {total} | Fires Detected: {fires} | Fire Rate: {accuracy:.1f}%")

    def show_statistics(self):
        """Show detailed statistics"""
        if not self.detection_history:
            messagebox.showinfo("Statistics", "No detection history available")
            return
        
        total = len(self.detection_history)
        fires = sum(1 for item in self.detection_history if item['has_fire'])
        avg_confidence = sum(item['confidence'] for item in self.detection_history) / total
        fire_confidence = sum(item['confidence'] for item in self.detection_history if item['has_fire']) / fires if fires > 0 else 0
        
        stats_text = f"""
📊 Detection Statistics:
────────────────────────
Total Detections: {total}
Fires Detected: {fires}
No Fire Cases: {total - fires}
Fire Detection Rate: {fires/total*100:.1f}%

Average Confidence: {avg_confidence:.2%}
Average Fire Confidence: {fire_confidence:.2%}

Detection Methods Used:
"""
        # Method usage statistics
        method_stats = {}
        for item in self.detection_history:
            method = item['method']
            method_stats[method] = method_stats.get(method, 0) + 1
        
        for method, count in method_stats.items():
            stats_text += f"  {method}: {count} times ({count/total*100:.1f}%)\n"
        
        messagebox.showinfo("Detailed Statistics", stats_text)

    # ALARM SYSTEM METHODS
    def trigger_alarm(self, has_fire, confidence):
        """Trigger alarm system when fire is detected"""
        if not has_fire or confidence < self.threshold_var.get():
            return
        
        if not self.alert_var.get():
            return
        
        self.alarm_active = True
        self.alarm_start_time = time.time()
        
        alarm_type = self.alarm_type_var.get()
        
        # Visual alarm
        if alarm_type in ["Visual", "Both"]:
            self.start_visual_alarm()
        
        # Sound alarm
        if alarm_type in ["Sound", "Both"] and self.sound_available:
            self.start_sound_alarm()
        
        # Show alarm notification
        self.show_alarm_notification(confidence)
        
        # Schedule alarm stop
        duration = self.alarm_duration_var.get() * 1000  # Convert to milliseconds
        self.root.after(duration, self.stop_alarm)
    
    def start_visual_alarm(self):
        """Start visual alarm (flashing)"""
        self.alarm_flash_count = 0
        self._flash_alarm_visual()
    
    def _flash_alarm_visual(self):
        """Flash the window and result label for visual alarm"""
        if not self.alarm_active:
            return
            
        if self.alarm_flash_count % 2 == 0:
            # Flash red
            self.root.configure(bg='red')
            self.result_var.set("🚨 FIRE ALARM! EVACUATE! 🚨")
        else:
            # Return to normal
            self.root.configure(bg='#0b66c2')
            self.result_var.set("🔥 FIRE DETECTED! 🔥")
        
        self.alarm_flash_count += 1
        
        # Continue flashing until alarm stops
        if self.alarm_active:
            self.root.after(500, self._flash_alarm_visual)
    
    def start_sound_alarm(self):
        """Start sound alarm in separate thread"""
        if self.alarm_sound_thread and self.alarm_sound_thread.is_alive():
            return
            
        self.alarm_sound_thread = threading.Thread(target=self._play_alarm_sound)
        self.alarm_sound_thread.daemon = True
        self.alarm_sound_thread.start()
    
    def _play_alarm_sound(self):
        """Play alarm sound based on selected type"""
        sound_type = self.alarm_sound_var.get()
        volume = self.alarm_volume_var.get()
        
        try:
            if sound_type == "Siren":
                self._play_siren_sound(volume)
            elif sound_type == "Beep":
                self._play_beep_sound(volume)
            elif sound_type == "Alert":
                self._play_alert_sound(volume)
            elif sound_type == "Emergency":
                self._play_emergency_sound(volume)
        except Exception as e:
            print(f"Sound error: {e}")
    
    def _play_siren_sound(self, volume):
        """Play siren sound using winsound or pygame"""
        duration = self.alarm_duration_var.get()
        start_time = time.time()
        
        while self.alarm_active and (time.time() - start_time) < duration:
            try:
                # Windows beep siren
                for freq in range(500, 1000, 50):
                    if not self.alarm_active:
                        break
                    winsound.Beep(freq, 100)
                for freq in range(1000, 500, -50):
                    if not self.alarm_active:
                        break
                    winsound.Beep(freq, 100)
            except:
                # Fallback: system beep
                self.root.bell()
                time.sleep(0.5)
    
    def _play_beep_sound(self, volume):
        """Play repetitive beep sound"""
        duration = self.alarm_duration_var.get()
        start_time = time.time()
        
        while self.alarm_active and (time.time() - start_time) < duration:
            self.root.bell()
            time.sleep(0.5)
    
    def _play_alert_sound(self, volume):
        """Play alert sound using pygame"""
        try:
            # Create a simple alert sound
            pygame.mixer.music.stop()
            
            # Generate a simple tone
            sample_rate = 44100
            duration = 0.5
            freq = 880
            
            samples = np.sin(2 * np.pi * np.arange(sample_rate * duration) * freq / sample_rate)
            samples = np.int16(samples * 32767 * volume)
            
            sound = pygame.sndarray.make_sound(samples)
            
            # Play repeatedly
            play_time = 0
            while self.alarm_active and play_time < self.alarm_duration_var.get():
                sound.play()
                time.sleep(0.8)
                play_time += 0.8
                
        except Exception as e:
            print(f"Alert sound error: {e}")
            self.root.bell()
    
    def _play_emergency_sound(self, volume):
        """Play emergency alarm pattern"""
        duration = self.alarm_duration_var.get()
        start_time = time.time()
        
        pattern = [('high', 0.3), ('silent', 0.1), ('high', 0.3), ('silent', 0.5)]
        
        while self.alarm_active and (time.time() - start_time) < duration:
            for note, note_duration in pattern:
                if not self.alarm_active:
                    break
                if note == 'high':
                    try:
                        winsound.Beep(1000, int(note_duration * 1000))
                    except:
                        self.root.bell()
                else:
                    time.sleep(note_duration)
    
    def show_alarm_notification(self, confidence):
        """Show alarm notification popup"""
        alarm_msg = f"""
🚨 FIRE ALARM TRIGGERED! 🚨

Fire detected with {confidence:.1%} confidence!

Immediate Action Required:
• Evacuate the area immediately
• Alert others in the vicinity
• Contact emergency services
• Use fire extinguisher if safe to do so

Alarm Type: {self.alarm_type_var.get()}
Duration: {self.alarm_duration_var.get()} seconds
        """
        
        # Create a top-level window for the alarm
        self.alarm_window = tk.Toplevel(self.root)
        self.alarm_window.title("🔥 FIRE ALARM 🔥")
        self.alarm_window.geometry("400x300")
        self.alarm_window.configure(bg='red')
        self.alarm_window.attributes('-topmost', True)
        
        # Alarm content
        alarm_label = tk.Label(self.alarm_window, text="🚨 FIRE ALARM! 🚨", 
                              font=("Arial", 20, "bold"), bg='red', fg='white')
        alarm_label.pack(pady=20)
        
        msg_label = tk.Label(self.alarm_window, text=alarm_msg, 
                            font=("Arial", 12), bg='red', fg='white', justify=tk.LEFT)
        msg_label.pack(pady=10)
        
        stop_button = tk.Button(self.alarm_window, text="STOP ALARM", 
                               command=self.stop_alarm, font=("Arial", 14, "bold"),
                               bg='white', fg='red', relief=tk.RAISED)
        stop_button.pack(pady=20)
    
    def stop_alarm(self):
        """Stop all alarm activities"""
        self.alarm_active = False
        
        # Reset visual elements
        self.root.configure(bg='#0b66c2')
        self.result_var.set("Alarm stopped")
        
        # Close alarm window if exists
        if hasattr(self, 'alarm_window') and self.alarm_window:
            try:
                self.alarm_window.destroy()
            except:
                pass
        
        self.status_var.set("Alarm stopped")
    
    def test_alarm(self):
        """Test the alarm system"""
        self.status_var.set("Testing alarm system...")
        self.trigger_alarm(True, 0.95)  # Simulate high confidence fire detection
    
    def on_method_change(self, event):
        self.current_method = self.method_var.get()
        self.status_var.set(f"Detection method changed to: {self.current_method}")

    # FIRE DETECTION METHODS
    def color_based_detection(self, image_path):
        """Real fire detection using color analysis"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return False, 0.0
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Define fire color ranges (red and orange)
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            lower_orange = np.array([11, 100, 100])
            upper_orange = np.array([25, 255, 255])
            
            # Create masks for fire colors
            mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
            
            fire_mask = mask_red1 + mask_red2 + mask_orange
            
            # Apply morphological operations to reduce noise
            kernel = np.ones((5, 5), np.uint8)
            fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_OPEN, kernel)
            fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_CLOSE, kernel)
            
            # Calculate percentage of fire-colored pixels
            total_pixels = image.shape[0] * image.shape[1]
            fire_pixels = np.count_nonzero(fire_mask)
            fire_ratio = fire_pixels / total_pixels
            
            # Dynamic threshold based on image size and characteristics
            base_threshold = 0.02  # 2% of image
            min_area_threshold = 100  # Minimum fire area in pixels
            
            has_fire = (fire_ratio > base_threshold) and (fire_pixels > min_area_threshold)
            confidence = min(fire_ratio * 10, 0.95)  # Scale confidence
            
            return has_fire, confidence
            
        except Exception as e:
            print(f"Color detection error: {e}")
            return False, 0.0

    def temperature_simulation_detection(self, image_path):
        """Simulate thermal imaging using color temperature"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return False, 0.0
            
            # Convert to LAB color space for better brightness analysis
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            
            # Analyze "hot" regions (bright areas with red tones)
            # High brightness in L channel combined with red in A channel
            _, bright_mask = cv2.threshold(l_channel, 200, 255, cv2.THRESH_BINARY)
            
            # Red areas have specific characteristics in A channel
            _, red_mask = cv2.threshold(a_channel, 130, 255, cv2.THRESH_BINARY)
            
            # Combine masks
            hot_mask = cv2.bitwise_and(bright_mask, red_mask)
            
            # Calculate hot area ratio
            total_pixels = image.shape[0] * image.shape[1]
            hot_pixels = np.count_nonzero(hot_mask)
            hot_ratio = hot_pixels / total_pixels
            
            has_fire = hot_ratio > 0.03  # 3% hot area threshold
            confidence = min(hot_ratio * 8, 0.90)
            
            return has_fire, confidence
            
        except Exception as e:
            print(f"Temperature detection error: {e}")
            return False, 0.0

    def motion_based_detection(self, image_path):
        """Simulate motion-based fire detection (for video sequences)"""
        try:
            # For single images, combine color and texture analysis
            image = cv2.imread(image_path)
            if image is None:
                return False, 0.0
            
            # Analyze texture using edge detection (fire has complex textures)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            
            # Fire-like regions have high edge density
            edge_density = np.count_nonzero(edges) / (image.shape[0] * image.shape[1])
            
            # Combine with color analysis
            has_fire_color, color_confidence = self.color_based_detection(image_path)
            
            # Combined confidence
            motion_confidence = min(edge_density * 5, 0.7)
            combined_confidence = (color_confidence * 0.7 + motion_confidence * 0.3)
            
            has_fire = combined_confidence > 0.4
            
            return has_fire, combined_confidence
            
        except Exception as e:
            print(f"Motion detection error: {e}")
            return False, 0.0

    def advanced_ai_detection(self, image_path):
        """Advanced detection combining multiple methods"""
        try:
            # Combine all detection methods for better accuracy
            results = []
            confidences = []
            
            # Method 1: Color-based
            fire1, conf1 = self.color_based_detection(image_path)
            results.append(fire1)
            confidences.append(conf1)
            
            # Method 2: Temperature simulation
            fire2, conf2 = self.temperature_simulation_detection(image_path)
            results.append(fire2)
            confidences.append(conf2)
            
            # Method 3: Motion/texture based
            fire3, conf3 = self.motion_based_detection(image_path)
            results.append(fire3)
            confidences.append(conf3)
            
            # Weighted decision
            total_confidence = sum(confidences) / len(confidences)
            fire_votes = sum(1 for i, fire in enumerate(results) if fire and confidences[i] > 0.3)
            
            has_fire = fire_votes >= 2  # At least 2 methods agree
            final_confidence = total_confidence * (1 + 0.1 * fire_votes)  # Boost confidence for agreement
            
            return has_fire, min(final_confidence, 0.99)
            
        except Exception as e:
            print(f"AI detection error: {e}")
            return False, 0.0

    def detect_fire_advanced(self, image_path):
        """Main detection function that uses the selected method"""
        method = self.current_method
        
        if method == "Color-Based":
            return self.color_based_detection(image_path)
        elif method == "Temperature Simulation":
            return self.temperature_simulation_detection(image_path)
        elif method == "Motion-Based":
            return self.motion_based_detection(image_path)
        elif method == "Advanced AI":
            return self.advanced_ai_detection(image_path)
        else:
            return self.color_based_detection(image_path)

    def create_processed_image(self, image_path, has_fire, confidence):
        """Create a visualization of the detection results"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Convert BGR to RGB for PIL
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Create a draw object
            draw = ImageDraw.Draw(pil_image)
            
            # Try to load a font, use default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 30)
            except:
                font = ImageFont.load_default()
            
            # Get image dimensions
            width, height = pil_image.size
            
            # Draw results based on detection
            if has_fire:
                # Red border and text for fire detected
                border_color = (255, 0, 0)  # Red
                text_color = (255, 255, 0)  # Yellow text
                status_text = "🔥 FIRE DETECTED! 🔥"
            else:
                # Green border and text for no fire
                border_color = (0, 255, 0)  # Green
                text_color = (0, 255, 255)  # Cyan text
                status_text = "✅ No Fire Detected"
            
            # Draw border
            draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=5)
            
            # Draw status text
            draw.rectangle([10, 10, width-10, 60], fill=(0, 0, 0, 128))
            draw.text((20, 15), status_text, fill=text_color, font=font)
            
            # Draw confidence
            conf_text = f"Confidence: {confidence:.2%} | Method: {self.current_method}"
            draw.rectangle([10, height-50, width-10, height-10], fill=(0, 0, 0, 128))
            draw.text((20, height-45), conf_text, fill=(255, 255, 255), font=font)
            
            # Convert back to base64 for display
            buffered = io.BytesIO()
            pil_image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return f"data:image/jpeg;base64,{img_str}"
            
        except Exception as e:
            print(f"Error creating processed image: {e}")
            return None

    def trigger_alert(self, has_fire, confidence):
        """Trigger visual and sound alerts for fire detection"""
        if not self.alert_var.get() or confidence < self.threshold_var.get():
            return
        
        if has_fire:
            # Trigger the full alarm system
            self.trigger_alarm(has_fire, confidence)
            
            # Show popup alert for high confidence fires
            if confidence > 0.8:
                messagebox.showwarning("FIRE ALERT!", 
                                      f"High confidence fire detected!\nConfidence: {confidence:.2%}\n\nPlease take immediate action!")

    # UI METHODS
    def browse_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image for Fire Detection",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("All files", "*.*")]
        )
        if file_path:
            self.image_path.set(file_path)
            self.display_image(file_path, self.original_image_label)
            self.status_var.set(f"Loaded: {os.path.basename(file_path)}")

    def display_image(self, image_path, label):
        try:
            image = Image.open(image_path)
            # Resize image to fit in the UI
            image.thumbnail((400, 400))
            photo = ImageTk.PhotoImage(image)
            label.configure(image=photo, text="")
            label.image = photo  # Keep a reference
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {e}")

    def detect_fire(self):
        image_path = self.image_path.get()
        if not image_path:
            messagebox.showwarning("Warning", "Please select an image first")
            return
        
        if not os.path.exists(image_path):
            messagebox.showerror("Error", "Selected image file does not exist")
            return
        
        # Show loading state
        self.result_var.set("Processing...")
        self.status_var.set(f"Detecting fire using {self.current_method}...")
        
        # Run detection in a separate thread
        thread = threading.Thread(target=self._detect_fire_thread, args=(image_path,))
        thread.daemon = True
        thread.start()

    def _detect_fire_thread(self, image_path):
        try:
            # Use advanced fire detection
            has_fire, confidence = self.detect_fire_advanced(image_path)
            
            # Get image name for history
            image_name = os.path.basename(image_path)
            
            # Create processed image visualization
            processed_image = self.create_processed_image(image_path, has_fire, confidence)
            
            result = {
                'success': True,
                'has_fire': has_fire,
                'confidence': confidence,
                'processed_image': processed_image,
                'image_name': image_name
            }
            
            self.root.after(0, self._update_detection_result, result)
                
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Detection failed: {e}")
            self.root.after(0, lambda: self.status_var.set("Detection failed"))

    def _update_detection_result(self, result):
        # Update result text
        if result['has_fire']:
            status = "🔥 FIRE DETECTED! 🔥"
            color = "red"
        else:
            status = "✅ No fire detected"
            color = "green"
        
        self.result_var.set(f"{status} (Confidence: {result['confidence']:.2%})")
        
        # Display processed image
        if result.get('processed_image'):
            self._display_base64_image(result['processed_image'], self.processed_image_label)
        else:
            self.processed_image_label.configure(text="Processed image not available", image='')
        
        # Save to history
        self.save_to_history(
            image_name=result.get('image_name', 'unknown.jpg'),
            has_fire=result['has_fire'],
            confidence=result['confidence']
        )
        
        # Trigger alerts
        self.trigger_alert(result['has_fire'], result['confidence'])
        
        self.status_var.set(f"Detection completed using {self.current_method}")

    def _display_base64_image(self, image_data, label):
        try:
            # Extract base64 data
            image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image.thumbnail((400, 400))
            photo = ImageTk.PhotoImage(image)
            label.configure(image=photo, text="")
            label.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error displaying processed image: {e}")

    def batch_process(self):
        """Process multiple images at once"""
        files = filedialog.askopenfilenames(
            title="Select Images for Batch Processing",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if not files:
            return
        
        self.status_var.set(f"Batch processing {len(files)} images...")
        
        def process_batch():
            results = []
            for i, file_path in enumerate(files):
                try:
                    has_fire, confidence = self.detect_fire_advanced(file_path)
                    results.append({
                        'file': os.path.basename(file_path),
                        'has_fire': has_fire,
                        'confidence': confidence
                    })
                    
                    # Update progress
                    self.root.after(0, lambda: self.status_var.set(
                        f"Processed {i+1}/{len(files)}: {os.path.basename(file_path)}"
                    ))
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
            
            # Show batch results
            self.root.after(0, self._show_batch_results, results)
        
        thread = threading.Thread(target=process_batch)
        thread.daemon = True
        thread.start()

    def _show_batch_results(self, results):
        fires = sum(1 for r in results if r['has_fire'])
        total = len(results)
        
        result_text = f"Batch Processing Complete!\n\n"
        result_text += f"Total images: {total}\n"
        result_text += f"Fires detected: {fires}\n"
        result_text += f"No fire: {total - fires}\n"
        result_text += f"Fire rate: {fires/total*100:.1f}%"
        
        messagebox.showinfo("Batch Processing Results", result_text)
        self.status_var.set(f"Batch complete: {fires} fires detected in {total} images")

    # WEBCAM METHODS
    def start_webcam(self):
        if self.webcam_running:
            return
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open webcam")
            return
        
        self.webcam_running = True
        self.status_var.set("Webcam started - Press 'Continuous Detection' for real-time monitoring")
        self._update_webcam_frame()

    def _update_webcam_frame(self):
        if self.webcam_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Convert frame to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert to PIL Image
                image = Image.fromarray(frame_rgb)
                image.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(image)
                self.original_image_label.configure(image=photo, text="")
                self.original_image_label.image = photo
                
                # Continuous detection
                if self.continuous_detection:
                    self._continuous_detect(frame)
                
                # Schedule next update
                self.root.after(50, self._update_webcam_frame)

    def _continuous_detect(self, frame):
        """Perform continuous detection on webcam frames"""
        try:
            # Save temporary image for detection
            temp_path = "temp_webcam.jpg"
            cv2.imwrite(temp_path, frame)
            
            # Quick detection (simplified for performance)
            has_fire, confidence = self.color_based_detection(temp_path)
            
            if has_fire and confidence > 0.5:
                # Update result display
                self.root.after(0, lambda: self.result_var.set(
                    f"LIVE: Fire detected! ({confidence:.1%})"
                ))
                
                # Trigger alert
                if self.alert_var.get():
                    self.root.after(0, lambda: self.trigger_alert(True, confidence))
            
        except Exception as e:
            print(f"Continuous detection error: {e}")

    def toggle_continuous_detection(self):
        if not self.webcam_running:
            messagebox.showwarning("Warning", "Please start webcam first")
            return
        
        self.continuous_detection = not self.continuous_detection
        status = "ENABLED" if self.continuous_detection else "DISABLED"
        self.status_var.set(f"Continuous detection {status}")

    def capture_webcam(self):
        if not self.webcam_running or not self.cap.isOpened():
            messagebox.showwarning("Warning", "Webcam is not active")
            return
        
        self.result_var.set("Capturing and processing webcam image...")
        self.status_var.set("Processing webcam capture...")
        
        # Capture current frame
        ret, frame = self.cap.read()
        if ret:
            # Save captured image
            temp_path = f"webcam_capture_{datetime.now().strftime('%H%M%S')}.jpg"
            cv2.imwrite(temp_path, frame)
            
            # Process the capture
            thread = threading.Thread(target=self._detect_fire_thread, args=(temp_path,))
            thread.daemon = True
            thread.start()

    def stop_webcam(self):
        self.webcam_running = False
        self.continuous_detection = False
        if self.cap:
            self.cap.release()
        self.original_image_label.configure(image='', text="Webcam stopped")
        self.original_image_label.image = None
        self.status_var.set("Webcam stopped")

if __name__ == "__main__":
    root = tk.Tk()
    app = FireDetectorApp(root)
    root.mainloop()