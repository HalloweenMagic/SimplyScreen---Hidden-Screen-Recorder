import cv2
import pyautogui
import numpy as np
import sounddevice as sd
import threading
import time
import os
import sys
import shutil
import subprocess
from datetime import datetime
import wave
from moviepy.editor import VideoFileClip, AudioFileClip
import logging
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import winreg
import tempfile

class RegistryManager:
    """Gestisce le operazioni del registro di Windows per l'avvio automatico"""
    
    def __init__(self):
        self.reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        self.app_name = "ScreenRecorderAuto"
    
    def is_in_startup(self):
        """Controlla se l'applicazione è già nel registro di avvio"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.reg_path) as key:
                try:
                    winreg.QueryValueEx(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False
        except Exception as e:
            print(f"Errore controllo registro: {e}")
            return False
    
    def add_to_startup(self, exe_path):
        """Aggiunge l'applicazione all'avvio automatico"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.reg_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
            return True
        except Exception as e:
            print(f"Errore aggiunta al registro: {e}")
            return False
    
    def remove_from_startup(self):
        """Rimuove l'applicazione dall'avvio automatico"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.reg_path, 0, winreg.KEY_WRITE) as key:
                try:
                    winreg.DeleteValue(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return True  # Era già rimosso
        except Exception as e:
            print(f"Errore rimozione dal registro: {e}")
            return False


class ConfigurationDialog:
    def __init__(self):
        self.result = None
        self.root = tk.Tk()
        self.registry_manager = RegistryManager()
        
        # Dizionario delle traduzioni
        self.translations = {
            'it': {
                'title': "Configurazione Screen Recorder",
                'subtitle': "Configura le impostazioni per la registrazione dello schermo",
                'language': "Lingua / Language",
                'output_dir': "Directory di Output",
                'output_info': "Directory principale dove salvare i video. Directory predefinita: C:\\Users\\[utente]\\Documents\\Docs",
                'browse': "Sfoglia...",
                'segment_duration': "Durata Segmenti Video",
                'duration_label': "Durata di ogni segmento video:",
                'seconds': "secondi",
                'duration_info': "Consigliato: 120 secondi (2 minuti). Valori più bassi = più file, valori più alti = file più grandi",
                'audio_device': "Dispositivo Audio",
                'audio_info': "Seleziona il dispositivo audio da utilizzare per la registrazione",
                'logging_options': "Opzioni Logging",
                'enable_logging': "Abilita file di log (salva eventi e errori in recorder.log)",
                'logging_info': "Se disabilitato, gli eventi verranno mostrati solo nella console",
                'startup_options': "Opzioni Avvio Automatico",
                'enable_startup': "Avvia automaticamente con Windows",
                'startup_info_title': "Informazioni Avvio Automatico",
                'startup_info_msg': "L'applicazione verrà configurata per avviarsi automaticamente all'accesso a Windows.\n\nUn eseguibile autonomo verrà creato e salvato in:\n%LOCALAPPDATA%\\ScreenRecorderAuto\n\nI file di configurazione saranno nella stessa directory.\n\nPuoi modificare questa impostazione in qualsiasi momento riaprendo la configurazione.",
                'startup_current_status': "Attualmente nell'avvio automatico:",
                'startup_enabled': "Abilitato",
                'startup_disabled': "Disabilitato",
                'cancel': "Annulla",
                'save_start': "Salva e Avvia",
                'note': "Nota: Queste impostazioni verranno salvate. Per riconfigurare, elimina il file 'nopopup.txt'",
                'error': "Errore",
                'cannot_create_dir': "Impossibile creare la directory:",
                'min_duration_error': "La durata minima del segmento è 30 secondi",
                'config_saved': "Configurazione Salvata",
                'config_saved_msg': "Configurazione salvata con successo!\n\nIl programma inizierà la registrazione tra poco.",
                'select_dir': "Seleziona directory di output",
                'no_audio_detected': "Nessun dispositivo audio rilevato",
                'audio_error': "Errore rilevamento dispositivi:",
                'creating_exe': "Creazione eseguibile...",
                'creating_exe_msg': "Sto creando l'eseguibile per l'avvio automatico.\nQuesto potrebbe richiedere alcuni minuti...",
                'exe_creation_error': "Errore nella creazione dell'eseguibile",
                'exe_creation_success': "Eseguibile creato con successo",
                'startup_setup_success': "Avvio automatico configurato con successo",
                'startup_setup_error': "Errore nella configurazione dell'avvio automatico",
                'startup_removed_success': "Avvio automatico rimosso con successo",
                'startup_removed_error': "Errore nella rimozione dell'avvio automatico",
                'config_dir_error': "Errore nella creazione della directory di configurazione",
                'pyinstaller_not_found': "PyInstaller non trovato. Installalo con: pip install pyinstaller",
                'desktop_summary': "Crea file riepilogativo sul desktop",
                'desktop_summary_info': "Crea un file di testo sul desktop con tutte le informazioni di configurazione e le istruzioni per gestire l'applicazione",
                'operations_completed': "Operazioni Completate",
                'summary_created': "File riepilogativo creato sul desktop",
                'summary_error': "Errore nella creazione del file riepilogativo",
                'deployment_options': "Opzioni Distribuzione",
                'deploy_local': "Installa su questo computer (avvio automatico)",
                'deploy_external': "Genera file .exe per uso esterno",
                'deployment_info': "Scegli se installare il programma su questo computer o generare un file .exe da usare su altri computer",
                'save_exe_title': "Salva file eseguibile",
                'exe_saved_success': "File .exe salvato con successo",
                'exe_saved_msg': "Il file eseguibile è stato salvato in:\n{}\n\nPuoi copiarlo su altri computer per l'uso.",
                'config_and_generate': "Configura e Genera",
                'generating_exe': "Generazione in corso...",
                'generating_exe_msg': "Sto generando il file .exe configurato.\nAttendi...",
                'external_startup_options': "Opzioni Avvio Automatico per Eseguibile Esterno",
                'external_enable_startup': "L'eseguibile si avvierà automaticamente con Windows",
                'external_disable_startup': "L'eseguibile funzionerà solo quando avviato manualmente",
                'external_startup_info': "Scegli se l'eseguibile, una volta copiato su un altro computer, deve configurarsi per l'avvio automatico o funzionare solo quando avviato manualmente",
                'startup_section': "Avvio Automatico",
                'startup_simple_info': "Se abilitato, il programma si avvierà automaticamente con Windows",
                'audio_recording': "Registrazione Audio",
                'enable_audio': "Registra audio del microfono",
                'audio_recording_info': "Se abilitato, verrà registrato anche l'audio del microfono insieme al video"
            },
            'en': {
                'title': "Screen Recorder Configuration",
                'subtitle': "Configure settings for screen recording",
                'language': "Lingua / Language",
                'output_dir': "Output Directory",
                'output_info': "Main directory to save videos. Default directory: C:\\Users\\[user]\\Documents\\Docs",
                'browse': "Browse...",
                'segment_duration': "Video Segment Duration",
                'duration_label': "Duration of each video segment:",
                'seconds': "seconds",
                'duration_info': "Recommended: 120 seconds (2 minutes). Lower values = more files, higher values = larger files",
                'audio_device': "Audio Device",
                'audio_info': "Select the audio device to use for recording",
                'logging_options': "Logging Options",
                'enable_logging': "Enable log file (saves events and errors to recorder.log)",
                'logging_info': "If disabled, events will only be shown in the console",
                'startup_options': "Startup Options",
                'enable_startup': "Start automatically with Windows",
                'startup_info_title': "Startup Information",
                'startup_info_msg': "The application will be configured to start automatically on Windows login.\n\nA standalone executable will be created and saved in:\n%LOCALAPPDATA%\\ScreenRecorderAuto\n\nConfiguration files will be in the same directory.\n\nYou can change this setting anytime by reopening the configuration.",
                'startup_current_status': "Currently in automatic startup:",
                'startup_enabled': "Enabled",
                'startup_disabled': "Disabled",
                'cancel': "Cancel",
                'save_start': "Save and Start",
                'note': "Note: These settings will be saved. To reconfigure, delete the 'nopopup.txt' file",
                'error': "Error",
                'cannot_create_dir': "Unable to create directory:",
                'min_duration_error': "The minimum segment duration is 30 seconds",
                'config_saved': "Configuration Saved",
                'config_saved_msg': "Configuration saved successfully!\n\nThe program will start recording shortly.",
                'select_dir': "Select output directory",
                'no_audio_detected': "No audio devices detected",
                'audio_error': "Device detection error:",
                'creating_exe': "Creating executable...",
                'creating_exe_msg': "Creating executable for startup.\nThis may take a few minutes...",
                'exe_creation_error': "Error creating executable",
                'exe_creation_success': "Executable created successfully",
                'startup_setup_success': "Startup configured successfully",
                'startup_setup_error': "Error configuring startup",
                'startup_removed_success': "Startup removed successfully",
                'startup_removed_error': "Error removing startup",
                'config_dir_error': "Error creating configuration directory",
                'pyinstaller_not_found': "PyInstaller not found. Install it with: pip install pyinstaller",
                'desktop_summary': "Create summary file on desktop",
                'desktop_summary_info': "Create a text file on the desktop with all configuration information and instructions for managing the application",
                'operations_completed': "Operations Completed",
                'summary_created': "Summary file created on desktop",
                'summary_error': "Error creating summary file",
                'deployment_options': "Deployment Options",
                'deploy_local': "Install on this computer (auto-startup)",
                'deploy_external': "Generate .exe file for external use",
                'deployment_info': "Choose whether to install the program on this computer or generate an .exe file to use on other computers",
                'save_exe_title': "Save executable file",
                'exe_saved_success': "Executable file saved successfully",
                'exe_saved_msg': "The executable file has been saved to:\n{}\n\nYou can copy it to other computers for use.",
                'config_and_generate': "Configure and Generate",
                'generating_exe': "Generating...",
                'generating_exe_msg': "Generating the configured .exe file.\nPlease wait...",
                'external_startup_options': "Auto-Startup Options for External Executable",
                'external_enable_startup': "The executable will start automatically with Windows",
                'external_disable_startup': "The executable will work only when started manually",
                'external_startup_info': "Choose whether the executable, once copied to another computer, should configure itself for automatic startup or work only when started manually",
                'startup_section': "Auto-Startup",
                'startup_simple_info': "If enabled, the program will start automatically with Windows",
                'audio_recording': "Audio Recording",
                'enable_audio': "Record microphone audio",
                'audio_recording_info': "If enabled, microphone audio will be recorded along with the video"
            }
        }
        
        # Lingua predefinita
        self.current_language = 'it'
        
        self.root.title(self.translations[self.current_language]['title'])
        self.root.geometry("700x700")
        self.root.resizable(True, True)
        self.root.minsize(650, 650)
        
        # Centra la finestra
        self.center_window()
        
        # Imposta l'icona della finestra (opzionale)
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # Variabili per i widget
        self.output_dir_var = tk.StringVar()
        self.segment_duration_var = tk.IntVar(value=120)
        self.audio_device_var = tk.StringVar()
        self.enable_logging_var = tk.BooleanVar(value=True)
        self.enable_startup_var = tk.BooleanVar(value=self.registry_manager.is_in_startup())
        self.create_desktop_summary_var = tk.BooleanVar(value=True)
        self.language_var = tk.StringVar(value='it')
        self.deployment_mode_var = tk.StringVar(value='local')  # 'local' o 'external'
        self.external_startup_var = tk.BooleanVar(value=True)  # Per eseguibili esterni
        self.enable_audio_var = tk.BooleanVar(value=True)  # Registrazione audio microfono
        
        # Riferimenti ai widget per l'aggiornamento delle traduzioni
        self.widgets = {}
        
        self.create_widgets()
    
    def get_config_directory(self):
        """Restituisce la directory per i file di configurazione"""
        config_dir = os.path.join(os.environ['LOCALAPPDATA'], 'ScreenRecorderAuto')
        try:
            os.makedirs(config_dir, exist_ok=True)
        except Exception as e:
            print(f"Errore creazione directory configurazione: {e}")
            # Fallback alla directory corrente
            config_dir = os.path.dirname(os.path.abspath(__file__))
        return config_dir
        
    def center_window(self):
        """Centra la finestra sullo schermo"""
        self.root.update_idletasks()
        width = 700
        height = 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def change_language(self, *args):
        """Cambia la lingua dell'interfaccia"""
        self.current_language = self.language_var.get()
        self.update_language()
    
    def update_language(self):
        """Aggiorna tutti i testi nell'interfaccia"""
        t = self.translations[self.current_language]
        
        self.root.title(t['title'])
        
        # Aggiorna tutti i widget salvati con gestione degli errori
        for key, widget in self.widgets.items():
            if key in t:
                try:
                    if isinstance(widget, ttk.Label):
                        widget.config(text=t[key])
                    elif isinstance(widget, ttk.LabelFrame):
                        widget.config(text=t[key])
                    elif isinstance(widget, ttk.Button):
                        widget.config(text=t[key])
                    elif isinstance(widget, ttk.Checkbutton):
                        widget.config(text=t[key])
                except tk.TclError:
                    # Widget potrebbe essere stato distrutto, ignora l'errore
                    pass
        
        # Aggiorna lo status dell'avvio automatico
        self.update_startup_status()
        self.root.update_idletasks()
    
    def show_startup_info(self):
        """Mostra le informazioni sull'avvio automatico"""
        t = self.translations[self.current_language]
        messagebox.showinfo(t['startup_info_title'], t['startup_info_msg'])

    def on_deployment_change(self):
        """Gestisce il cambio di modalità di distribuzione"""
        # Ora l'avvio automatico è unificato, non serve più gestire frames separati
        pass
    
    def update_startup_status(self):
        """Aggiorna la visualizzazione dello stato dell'avvio automatico"""
        if hasattr(self, 'startup_status_label'):
            t = self.translations[self.current_language]
            current_status = self.registry_manager.is_in_startup()
            status_text = t['startup_enabled'] if current_status else t['startup_disabled']
            self.startup_status_label.config(
                text=f"{t['startup_current_status']} {status_text}",
                foreground='green' if current_status else 'red'
            )
    
    def create_widgets(self):
        """Crea l'interfaccia grafica riorganizzata"""
        t = self.translations[self.current_language]

        # Titolo
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10, padx=20, fill='x')

        self.widgets['title'] = ttk.Label(title_frame, text=t['title'],
                               font=('Arial', 14, 'bold'))
        self.widgets['title'].pack()

        self.widgets['subtitle'] = ttk.Label(title_frame, text=t['subtitle'],
                                 font=('Arial', 9))
        self.widgets['subtitle'].pack(pady=(3, 0))

        # Frame principale con scroll se necessario
        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=10, padx=20, fill='both', expand=True)

        # 1. SELEZIONE LINGUA (prima cosa)
        lang_frame = ttk.LabelFrame(main_frame, text=t['language'], padding=8)
        lang_frame.pack(fill='x', pady=(0, 10))
        self.widgets['language'] = lang_frame

        self.language_var.trace('w', self.change_language)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.language_var,
                                 values=['it', 'en'], state='readonly', width=15)
        lang_combo.pack(anchor='w')
        lang_combo.set('it')

        # 2. TIPO DI DISTRIBUZIONE (seconda cosa)
        deployment_frame = ttk.LabelFrame(main_frame, text=t['deployment_options'], padding=8)
        deployment_frame.pack(fill='x', pady=(0, 10))
        self.widgets['deployment_options'] = deployment_frame

        self.widgets['deploy_local'] = ttk.Radiobutton(deployment_frame, text=t['deploy_local'],
                                      variable=self.deployment_mode_var, value='local',
                                      command=self.on_deployment_change)
        self.widgets['deploy_local'].pack(anchor='w', pady=(0, 3))

        self.widgets['deploy_external'] = ttk.Radiobutton(deployment_frame, text=t['deploy_external'],
                                      variable=self.deployment_mode_var, value='external',
                                      command=self.on_deployment_change)
        self.widgets['deploy_external'].pack(anchor='w')

        # 3. AVVIO AUTOMATICO (terza cosa - semplificata)
        startup_frame = ttk.LabelFrame(main_frame, text=t['startup_section'], padding=8)
        startup_frame.pack(fill='x', pady=(0, 10))
        self.widgets['startup_section'] = startup_frame

        self.widgets['enable_startup'] = ttk.Checkbutton(startup_frame, text=t['enable_startup'],
                                      variable=self.enable_startup_var)
        self.widgets['enable_startup'].pack(anchor='w')

        self.widgets['startup_simple_info'] = ttk.Label(startup_frame, text=t['startup_simple_info'],
                              font=('Arial', 8), foreground='gray', wraplength=600, justify='left')
        self.widgets['startup_simple_info'].pack(pady=(3, 0), fill='x')

        # 4. DURATA SEGMENTI (quarta cosa)
        duration_frame = ttk.LabelFrame(main_frame, text=t['segment_duration'], padding=8)
        duration_frame.pack(fill='x', pady=(0, 10))
        self.widgets['segment_duration'] = duration_frame

        duration_inner = ttk.Frame(duration_frame)
        duration_inner.pack(fill='x')

        self.widgets['duration_label'] = ttk.Label(duration_inner, text=t['duration_label'])
        self.widgets['duration_label'].pack(side='left')

        duration_spinbox = ttk.Spinbox(duration_inner, from_=30, to=600, width=10,
                                     textvariable=self.segment_duration_var)
        duration_spinbox.pack(side='right')

        self.widgets['seconds'] = ttk.Label(duration_inner, text=t['seconds'])
        self.widgets['seconds'].pack(side='right', padx=(5, 10))

        # 5. DIRECTORY DI OUTPUT (quinta cosa)
        output_frame = ttk.LabelFrame(main_frame, text=t['output_dir'], padding=8)
        output_frame.pack(fill='x', pady=(0, 10))
        self.widgets['output_dir'] = output_frame

        dir_frame = ttk.Frame(output_frame)
        dir_frame.pack(fill='x')

        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=50, state='readonly')
        self.dir_entry.pack(side='left', fill='x', expand=True)

        self.widgets['browse'] = ttk.Button(dir_frame, text=t['browse'], command=self.browse_directory)
        self.widgets['browse'].pack(side='right', padx=(10, 0))

        # Info directory
        self.widgets['output_info'] = ttk.Label(output_frame, text=t['output_info'],
                              font=('Arial', 8), foreground='gray', wraplength=600, justify='left')
        self.widgets['output_info'].pack(pady=(3, 0), fill='x')

        # 6. REGISTRAZIONE AUDIO (sesta cosa)
        audio_frame = ttk.LabelFrame(main_frame, text=t['audio_recording'], padding=8)
        audio_frame.pack(fill='x', pady=(0, 10))
        self.widgets['audio_recording'] = audio_frame

        self.widgets['enable_audio'] = ttk.Checkbutton(audio_frame, text=t['enable_audio'],
                                      variable=self.enable_audio_var)
        self.widgets['enable_audio'].pack(anchor='w')

        self.widgets['audio_recording_info'] = ttk.Label(audio_frame, text=t['audio_recording_info'],
                              font=('Arial', 8), foreground='gray', wraplength=600, justify='left')
        self.widgets['audio_recording_info'].pack(pady=(3, 0), fill='x')

        # 7. RIEPILOGO DESKTOP (settima cosa)
        desktop_frame = ttk.LabelFrame(main_frame, text=t['desktop_summary'], padding=8)
        desktop_frame.pack(fill='x', pady=(0, 10))

        self.widgets['enable_desktop_summary'] = ttk.Checkbutton(desktop_frame, text=t['desktop_summary'],
                                      variable=self.create_desktop_summary_var)
        self.widgets['enable_desktop_summary'].pack(anchor='w')

        # Imposta valori predefiniti
        self.output_dir_var.set(self.get_default_output_dir())
        self.detect_audio_devices()
        if self.audio_devices:
            self.audio_device_var.set(self.audio_devices[0])

        # Frame per i pulsanti
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=15, padx=20, side='bottom', fill='x')

        button_inner = ttk.Frame(button_frame)
        button_inner.pack()

        self.widgets['cancel'] = ttk.Button(button_inner, text=t['cancel'], command=self.cancel)
        self.widgets['cancel'].pack(side='left', padx=(0, 10))
        self.widgets['save_start'] = ttk.Button(button_inner, text=t['config_and_generate'], command=self.save_config)
        self.widgets['save_start'].pack(side='left')
    
    def get_default_output_dir(self):
        """Restituisce la directory di output predefinita"""
        # Directory predefinita fissa
        preferred_dir = os.path.join(os.path.expanduser("~"), "Documents", "Docs")
        
        # Crea la directory se non esiste
        os.makedirs(preferred_dir, exist_ok=True)
        
        return preferred_dir
    
    def detect_audio_devices(self):
        """Rileva i dispositivi audio disponibili"""
        t = self.translations[self.current_language]
        try:
            devices = sd.query_devices()
            self.audio_devices = []
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:  # Solo dispositivi di input
                    device_name = f"{i}: {device['name']}"
                    self.audio_devices.append(device_name)
            
            if not self.audio_devices:
                self.audio_devices = [t['no_audio_detected']]
                
        except Exception as e:
            self.audio_devices = [f"{t['audio_error']} {str(e)}"]
    
    def browse_directory(self):
        """Apre il dialog per selezionare la directory"""
        t = self.translations[self.current_language]
        
        # Temporaneamente disabilita il pulsante per evitare click multipli
        self.widgets['browse'].config(state='disabled')
        
        try:
            directory = filedialog.askdirectory(
                title=t['select_dir'],
                initialdir=self.output_dir_var.get(),
                parent=self.root
            )
            if directory:
                self.output_dir_var.set(directory)
        except Exception as e:
            print(f"Errore nella selezione directory: {e}")
        finally:
            # Riabilita il pulsante
            self.widgets['browse'].config(state='normal')
            # Forza l'aggiornamento della finestra
            self.root.update_idletasks()
    
    def create_executable(self):
        """Crea l'eseguibile usando PyInstaller"""
        t = self.translations[self.current_language]
        
        try:
            # Verifica se PyInstaller è disponibile
            try:
                import PyInstaller
            except ImportError:
                messagebox.showerror(t['error'], t['pyinstaller_not_found'])
                return False
            
            # Mostra dialog di progresso
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title(t['creating_exe'])
            progress_dialog.geometry("400x100")
            progress_dialog.transient(self.root)
            progress_dialog.grab_set()
            
            # Centra il dialog
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 50
            progress_dialog.geometry(f"400x120+{x}+{y}")
            
            ttk.Label(progress_dialog, text=t['creating_exe_msg']).pack(pady=15)
            progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
            progress_bar.pack(pady=10, padx=20, fill='x')
            progress_bar.start()
            
            self.root.update()
            
            # Ottieni il percorso dello script corrente
            script_path = os.path.abspath(__file__)
            script_dir = os.path.dirname(script_path)
            script_name = os.path.splitext(os.path.basename(script_path))[0]
            
            # Comando PyInstaller con directory di lavoro nella destinazione finale
            build_dir = os.path.join(script_dir, 'build')
            dist_dir = script_dir
            
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--onefile',
                '--noconsole',
                '--distpath', dist_dir,
                '--workpath', build_dir,
                '--specpath', script_dir,
                '--name', 'ScreenRecorderAuto',
                script_path
            ]
            
            # Esegui PyInstaller
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)
            
            progress_dialog.destroy()
            
            if result.returncode == 0:
                exe_path = os.path.join(script_dir, 'ScreenRecorderAuto.exe')
                if os.path.exists(exe_path):
                    messagebox.showinfo(t['exe_creation_success'], 
                                      f"{t['exe_creation_success']}\n\nPercorso: {exe_path}")
                    return exe_path
                else:
                    messagebox.showerror(t['exe_creation_error'], 
                                       f"{t['exe_creation_error']}\nFile exe non trovato")
                    return False
            else:
                messagebox.showerror(t['exe_creation_error'], 
                                   f"{t['exe_creation_error']}\n\n{result.stderr}")
                return False
                
        except Exception as e:
            messagebox.showerror(t['exe_creation_error'], f"{t['exe_creation_error']}\n\n{str(e)}")
            return False
    
    def create_desktop_summary_file(self, config, config_dir):
        """Crea un file riepilogativo sul desktop dell'utente"""
        t = self.translations[self.current_language]
        
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            summary_filename = f"{t['operations_completed']}.txt"
            summary_path = os.path.join(desktop_path, summary_filename)
            
            # Prepara il contenuto del file
            if self.current_language == 'it':
                content = self.create_italian_summary(config, config_dir)
            else:
                content = self.create_english_summary(config, config_dir)
            
            # Scrivi il file
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Mostra messaggio di conferma
            messagebox.showinfo(t['summary_created'], 
                              f"{t['summary_created']}\n\nPercorso: {summary_path}")
            
        except Exception as e:
            messagebox.showerror(t['summary_error'], f"{t['summary_error']}: {str(e)}")
    
    def create_italian_summary(self, config, config_dir):
        """Crea il contenuto del riepilogo in italiano"""
        exe_path = os.path.join(config_dir, 'ScreenRecorderAuto.exe')
        startup_status = "SÌ" if config.get('enable_startup', False) else "NO"
        
        content = f"""OPERAZIONI COMPLETATE - Screen Recorder
============================================

Data configurazione: {datetime.now().strftime('%d/%m/%Y alle %H:%M:%S')}

RIEPILOGO CONFIGURAZIONE:
========================

✓ Directory video: {config.get('output_dir', 'Non specificata')}
✓ Durata segmenti: {config.get('segment_duration', 120)} secondi
✓ Dispositivo audio: {config.get('audio_device_name', 'Predefinito')}
✓ Logging abilitato: {'SÌ' if config.get('enable_logging', True) else 'NO'}
✓ Avvio automatico Windows: {startup_status}
✓ Lingua interfaccia: {'Italiano' if config.get('language', 'it') == 'it' else 'Inglese'}

FILES INSTALLATI:
================

Eseguibile principale:
{exe_path}

File di configurazione:
{os.path.join(config_dir, 'config.json')}

File controllo popup:
{os.path.join(config_dir, 'nopopup.txt')}

Directory file log (se abilitato):
{config.get('output_dir', 'Non specificata')}\\recorder.log

ISTRUZIONI PER L'UTENTE:
=======================

🔧 COME RIAPRIRE LA GUI DI CONFIGURAZIONE:
   1. Vai in: {config_dir}
   2. Elimina il file: nopopup.txt
   3. Esegui: ScreenRecorderAuto.exe
   
🔄 COME ATTIVARE/DISATTIVARE AVVIO AUTOMATICO:
   - Metodo 1 (Consigliato): Riapri la GUI (vedi sopra) e cambia l'impostazione
   - Metodo 2 (Avanzato): 
     * Premi Win+R, digita: regedit
     * Vai in: HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run
     * Cerca la voce: ScreenRecorderAuto
     * Elimina per disattivare, ricrea per riattivare

📁 COME TROVARE I VIDEO REGISTRATI:
   I video vengono salvati in: {config.get('output_dir', 'Directory non specificata')}

🗑️ COME DISINSTALLARE COMPLETAMENTE:
   1. Disattiva l'avvio automatico (vedi sopra)
   2. Elimina la cartella: {config_dir}
   3. Elimina questo file dal desktop

⚙️ COME FUNZIONA IL PROGRAMMA:
   - Il programma registra automaticamente lo schermo in segmenti
   - Ogni segmento dura {config.get('segment_duration', 120)} secondi
   - I file vengono salvati con timestamp (giorno-mese-anno_ora-minuti-secondi)
   - Audio e video vengono combinati automaticamente in file MP4

📞 SUPPORTO:
   Se il programma non funziona correttamente:
   1. Controlla il file di log in: {config.get('output_dir', '[directory video]')}\\recorder.log
   2. Riavvia il programma
   3. Se necessario, riconfigura eliminando nopopup.txt

NOTA IMPORTANTE: Questo file può essere eliminato una volta lette le informazioni.
Il programma continuerà a funzionare normalmente.

Generato automaticamente da Screen Recorder v1.0
"""
        return content
    
    def create_english_summary(self, config, config_dir):
        """Crea il contenuto del riepilogo in inglese"""
        exe_path = os.path.join(config_dir, 'ScreenRecorderAuto.exe')
        startup_status = "YES" if config.get('enable_startup', False) else "NO"
        
        content = f"""OPERATIONS COMPLETED - Screen Recorder
=====================================

Configuration date: {datetime.now().strftime('%m/%d/%Y at %H:%M:%S')}

CONFIGURATION SUMMARY:
=====================

✓ Video directory: {config.get('output_dir', 'Not specified')}
✓ Segment duration: {config.get('segment_duration', 120)} seconds
✓ Audio device: {config.get('audio_device_name', 'Default')}
✓ Logging enabled: {'YES' if config.get('enable_logging', True) else 'NO'}
✓ Windows startup: {startup_status}
✓ Interface language: {'Italian' if config.get('language', 'it') == 'it' else 'English'}

INSTALLED FILES:
===============

Main executable:
{exe_path}

Configuration file:
{os.path.join(config_dir, 'config.json')}

Popup control file:
{os.path.join(config_dir, 'nopopup.txt')}

Log file directory (if enabled):
{config.get('output_dir', 'Not specified')}\\recorder.log

USER INSTRUCTIONS:
=================

🔧 HOW TO REOPEN THE CONFIGURATION GUI:
   1. Go to: {config_dir}
   2. Delete the file: nopopup.txt
   3. Run: ScreenRecorderAuto.exe
   
🔄 HOW TO ENABLE/DISABLE AUTOMATIC STARTUP:
   - Method 1 (Recommended): Reopen the GUI (see above) and change the setting
   - Method 2 (Advanced): 
     * Press Win+R, type: regedit
     * Navigate to: HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run
     * Look for entry: ScreenRecorderAuto
     * Delete to disable, recreate to enable

📁 HOW TO FIND RECORDED VIDEOS:
   Videos are saved in: {config.get('output_dir', 'Directory not specified')}

🗑️ HOW TO COMPLETELY UNINSTALL:
   1. Disable automatic startup (see above)
   2. Delete the folder: {config_dir}
   3. Delete this file from the desktop

⚙️ HOW THE PROGRAM WORKS:
   - The program automatically records the screen in segments
   - Each segment lasts {config.get('segment_duration', 120)} seconds
   - Files are saved with timestamp (day-month-year_hour-minutes-seconds)
   - Audio and video are automatically combined into MP4 files

📞 SUPPORT:
   If the program doesn't work correctly:
   1. Check the log file at: {config.get('output_dir', '[video directory]')}\\recorder.log
   2. Restart the program
   3. If needed, reconfigure by deleting nopopup.txt

IMPORTANT NOTE: This file can be deleted once you've read the information.
The program will continue to work normally.

Automatically generated by Screen Recorder v1.0
"""
        return content
    
    def setup_startup_registry(self, config_dir):
        """Configura l'avvio automatico tramite registro"""
        t = self.translations[self.current_language]
        
        try:
            if self.enable_startup_var.get():
                # Crea l'eseguibile e copialo nella directory di configurazione
                exe_path = self.create_and_deploy_executable(config_dir)
                if not exe_path:
                    return False

                # Crea il comando per l'avvio automatico
                startup_command = f'"{exe_path}" --config-dir "{config_dir}"'

                # Aggiungi al registro
                success = self.registry_manager.add_to_startup(startup_command)
                if success:
                    messagebox.showinfo(t['startup_setup_success'],
                                      f"{t['startup_setup_success']}\n\nEseguibile: {exe_path}")

                    # Avvia l'eseguibile per iniziare subito la registrazione
                    self.start_generated_executable(exe_path, config_dir)
                else:
                    messagebox.showerror(t['startup_setup_error'], t['startup_setup_error'])
                return success
            else:
                # Rimuovi dal registro
                success = self.registry_manager.remove_from_startup()
                
                # Rimuovi anche l'eseguibile dalla directory di configurazione se esiste
                exe_path = os.path.join(config_dir, 'ScreenRecorderAuto.exe')
                try:
                    if os.path.exists(exe_path):
                        os.remove(exe_path)
                        self.log_message(f"Eseguibile rimosso: {exe_path}")
                except Exception as e:
                    print(f"Avviso: impossibile rimuovere eseguibile: {e}")
                
                if success:
                    messagebox.showinfo(t['startup_removed_success'], t['startup_removed_success'])
                else:
                    messagebox.showerror(t['startup_removed_error'], t['startup_removed_error'])
                return success
                
        except Exception as e:
            messagebox.showerror(t['startup_setup_error'], f"{t['startup_setup_error']}: {str(e)}")
            return False
    
    def generate_external_executable(self, config):
        """Genera un eseguibile per uso esterno e chiede dove salvarlo"""
        t = self.translations[self.current_language]

        try:
            # Verifica se PyInstaller è disponibile
            try:
                import PyInstaller
            except ImportError:
                messagebox.showerror(t['error'], t['pyinstaller_not_found'])
                return False

            # Chiedi all'utente dove salvare l'eseguibile
            save_path = filedialog.asksaveasfilename(
                title=t['save_exe_title'],
                defaultextension=".exe",
                filetypes=[("Eseguibili", "*.exe"), ("Tutti i file", "*.*")],
                initialfile="ScreenRecorderAuto.exe"
            )

            if not save_path:
                return False  # L'utente ha annullato

            # Crea una directory temporanea per la configurazione
            temp_config_dir = tempfile.mkdtemp(prefix="screen_recorder_")

            try:
                # Modifica la configurazione per includere l'opzione di avvio automatico
                # scelta dall'utente (ora unificata per entrambe le modalità)
                external_config = config.copy()
                external_config['enable_startup'] = self.enable_startup_var.get()

                # Salva la configurazione nella directory temporanea
                config_path = os.path.join(temp_config_dir, 'config.json')
                with open(config_path, 'w') as f:
                    json.dump(external_config, f, indent=4)

                # Crea il file nopopup nella directory temporanea
                nopopup_path = os.path.join(temp_config_dir, 'nopopup.txt')
                with open(nopopup_path, 'w') as f:
                    f.write(f"Configurazione completata il {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("File creato per evitare il popup di configurazione")

                # Mostra dialog di progresso
                progress_dialog = tk.Toplevel(self.root)
                progress_dialog.title(t['generating_exe'])
                progress_dialog.geometry("400x120")
                progress_dialog.transient(self.root)
                progress_dialog.grab_set()

                # Centra il dialog
                x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
                y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 60
                progress_dialog.geometry(f"400x120+{x}+{y}")

                ttk.Label(progress_dialog, text=t['generating_exe_msg']).pack(pady=15)
                progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
                progress_bar.pack(pady=10, padx=20, fill='x')
                progress_bar.start()

                self.root.update()

                # Ottieni il percorso dello script corrente
                script_path = os.path.abspath(__file__)
                script_dir = os.path.dirname(script_path)

                # Directory temporanea per PyInstaller
                temp_build_dir = os.path.join(script_dir, 'temp_build_external')
                temp_dist_dir = os.path.join(script_dir, 'temp_dist_external')

                # Crea un file spec temporaneo per gestire meglio i dati aggiuntivi
                spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['{script_path.replace(os.sep, "/")}'],
    pathex=[],
    binaries=[],
    datas=[
        ('{config_path.replace(os.sep, "/")}', '.'),
        ('{nopopup_path.replace(os.sep, "/")}', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ScreenRecorderAuto',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

                # Salva il file spec temporaneo
                spec_file_path = os.path.join(script_dir, 'temp_external.spec')
                with open(spec_file_path, 'w', encoding='utf-8') as f:
                    f.write(spec_content)

                # Comando PyInstaller usando il file spec
                cmd = [
                    sys.executable, '-m', 'PyInstaller',
                    '--distpath', temp_dist_dir,
                    '--workpath', temp_build_dir,
                    spec_file_path
                ]

                # Esegui PyInstaller
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)

                progress_dialog.destroy()

                if result.returncode == 0:
                    temp_exe_path = os.path.join(temp_dist_dir, 'ScreenRecorderAuto.exe')

                    if os.path.exists(temp_exe_path):
                        # Copia l'eseguibile nella posizione scelta dall'utente
                        shutil.copy2(temp_exe_path, save_path)

                        # Pulisci i file temporanei
                        try:
                            shutil.rmtree(temp_build_dir, ignore_errors=True)
                            shutil.rmtree(temp_dist_dir, ignore_errors=True)
                            shutil.rmtree(temp_config_dir, ignore_errors=True)
                            # Rimuovi il file spec temporaneo
                            if os.path.exists(spec_file_path):
                                os.remove(spec_file_path)
                        except Exception as e:
                            print(f"Avviso: impossibile rimuovere file temporanei: {e}")

                        # Messaggio personalizzato per eseguibili esterni
                        startup_enabled = self.enable_startup_var.get()

                        if self.current_language == 'it':
                            startup_text = "• Si configurerà per l'avvio automatico" if startup_enabled else "• NON si configurerà per l'avvio automatico (solo avvio manuale)"
                            message = f"File .exe salvato con successo in:\n{save_path}\n\n" \
                                     "IMPORTANTE: Quando questo file verrà eseguito su un altro computer:\n" \
                                     "• Si installerà automaticamente nella directory di sistema\n" \
                                     f"{startup_text}\n" \
                                     "• Inizierà immediatamente la registrazione dello schermo\n\n" \
                                     "Non è necessaria alcuna configurazione aggiuntiva."
                        else:
                            startup_text = "• It will configure itself for automatic startup" if startup_enabled else "• It will NOT configure itself for automatic startup (manual start only)"
                            message = f"Executable file saved successfully to:\n{save_path}\n\n" \
                                     "IMPORTANT: When this file is run on another computer:\n" \
                                     "• It will automatically install itself in the system directory\n" \
                                     f"{startup_text}\n" \
                                     "• It will immediately start screen recording\n\n" \
                                     "No additional configuration is required."

                        messagebox.showinfo(t['exe_saved_success'], message)
                        return True

                    else:
                        messagebox.showerror(t['exe_creation_error'],
                                           f"{t['exe_creation_error']}\nFile exe non trovato")
                        return False
                else:
                    messagebox.showerror(t['exe_creation_error'],
                                       f"{t['exe_creation_error']}\n\n{result.stderr}")
                    return False

            finally:
                # Assicurati di pulire la directory temporanea e il file spec
                try:
                    shutil.rmtree(temp_config_dir, ignore_errors=True)
                    # Pulisci anche le directory temporanee di PyInstaller se esistono
                    if 'temp_build_dir' in locals():
                        shutil.rmtree(temp_build_dir, ignore_errors=True)
                    if 'temp_dist_dir' in locals():
                        shutil.rmtree(temp_dist_dir, ignore_errors=True)
                    if 'spec_file_path' in locals() and os.path.exists(spec_file_path):
                        os.remove(spec_file_path)
                except:
                    pass

        except Exception as e:
            messagebox.showerror(t['exe_creation_error'], f"{t['exe_creation_error']}\n\n{str(e)}")
            return False

    def create_and_deploy_executable(self, config_dir):
        """Crea l'eseguibile e lo copia nella directory di configurazione"""
        t = self.translations[self.current_language]
        
        try:
            # Verifica se PyInstaller è disponibile
            try:
                import PyInstaller
            except ImportError:
                messagebox.showerror(t['error'], t['pyinstaller_not_found'])
                return False
            
            # Mostra dialog di progresso
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title(t['creating_exe'])
            progress_dialog.geometry("400x120")
            progress_dialog.transient(self.root)
            progress_dialog.grab_set()
            
            # Centra il dialog
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 60
            progress_dialog.geometry(f"400x120+{x}+{y}")
            
            ttk.Label(progress_dialog, text=t['creating_exe_msg']).pack(pady=15)
            progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
            progress_bar.pack(pady=10, padx=20, fill='x')
            progress_bar.start()
            
            self.root.update()
            
            # Ottieni il percorso dello script corrente
            script_path = os.path.abspath(__file__)
            script_dir = os.path.dirname(script_path)
            
            # Directory temporanea per PyInstaller
            temp_build_dir = os.path.join(script_dir, 'temp_build')
            temp_dist_dir = os.path.join(script_dir, 'temp_dist')
            
            # Comando PyInstaller
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--onefile',
                '--noconsole',
                '--distpath', temp_dist_dir,
                '--workpath', temp_build_dir,
                '--specpath', script_dir,
                '--name', 'ScreenRecorderAuto',
                script_path
            ]
            
            # Esegui PyInstaller
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)
            
            progress_dialog.destroy()
            
            if result.returncode == 0:
                temp_exe_path = os.path.join(temp_dist_dir, 'ScreenRecorderAuto.exe')
                final_exe_path = os.path.join(config_dir, 'ScreenRecorderAuto.exe')
                
                if os.path.exists(temp_exe_path):
                    # Copia l'eseguibile nella directory di configurazione
                    try:
                        shutil.copy2(temp_exe_path, final_exe_path)
                        
                        # Pulisci i file temporanei
                        try:
                            shutil.rmtree(temp_build_dir, ignore_errors=True)
                            shutil.rmtree(temp_dist_dir, ignore_errors=True)
                            # Rimuovi anche il file .spec se esiste
                            spec_file = os.path.join(script_dir, 'ScreenRecorderAuto.spec')
                            if os.path.exists(spec_file):
                                os.remove(spec_file)
                        except Exception as e:
                            print(f"Avviso: impossibile rimuovere file temporanei: {e}")
                        
                        messagebox.showinfo(t['exe_creation_success'], 
                                          f"{t['exe_creation_success']}\n\nPercorso: {final_exe_path}")
                        return final_exe_path
                        
                    except Exception as e:
                        messagebox.showerror(t['exe_creation_error'], 
                                           f"Errore nella copia dell'eseguibile: {e}")
                        return False
                else:
                    messagebox.showerror(t['exe_creation_error'], 
                                       f"{t['exe_creation_error']}\nFile exe non trovato in: {temp_exe_path}")
                    return False
            else:
                messagebox.showerror(t['exe_creation_error'], 
                                   f"{t['exe_creation_error']}\n\n{result.stderr}")
                return False
                
        except Exception as e:
            messagebox.showerror(t['exe_creation_error'], f"{t['exe_creation_error']}\n\n{str(e)}")
            return False

    def start_generated_executable(self, exe_path, config_dir):
        """Avvia l'eseguibile generato per iniziare la registrazione"""
        t = self.translations[self.current_language]

        try:
            # Avvia l'eseguibile con la directory di configurazione specificata
            command = [exe_path, '--config-dir', config_dir]

            # Avvia il processo in background
            if os.name == 'nt':  # Windows
                subprocess.Popen(command,
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                               close_fds=True)
            else:  # Altri sistemi
                subprocess.Popen(command, start_new_session=True)

            # Mostra messaggio di conferma
            if self.current_language == 'it':
                message = "L'eseguibile è stato avviato!\n\nLa registrazione dello schermo inizierà tra poco.\nPuoi chiudere questa finestra."
            else:
                message = "The executable has been started!\n\nScreen recording will begin shortly.\nYou can close this window."

            messagebox.showinfo("Avvio Completato" if self.current_language == 'it' else "Startup Complete", message)

        except Exception as e:
            error_msg = f"Errore nell'avvio dell'eseguibile: {str(e)}" if self.current_language == 'it' else f"Error starting executable: {str(e)}"
            messagebox.showerror(t['error'], error_msg)

    def save_config(self):
        """Salva la configurazione e gestisce la generazione dell'eseguibile"""
        t = self.translations[self.current_language]

        # Validazione
        if not os.path.exists(self.output_dir_var.get()):
            try:
                os.makedirs(self.output_dir_var.get(), exist_ok=True)
            except Exception as e:
                messagebox.showerror(t['error'], f"{t['cannot_create_dir']} {e}")
                return

        if self.segment_duration_var.get() < 30:
            messagebox.showerror(t['error'], t['min_duration_error'])
            return

        # Estrae l'ID del dispositivo audio
        audio_device_id = None
        if self.audio_device_var.get() and ":" in self.audio_device_var.get():
            try:
                audio_device_id = int(self.audio_device_var.get().split(":")[0])
            except ValueError:
                audio_device_id = None

        config = {
            'output_dir': self.output_dir_var.get(),
            'segment_duration': self.segment_duration_var.get(),
            'audio_device_id': audio_device_id,
            'audio_device_name': self.audio_device_var.get(),
            'enable_logging': self.enable_logging_var.get(),
            'language': self.current_language,
            'enable_startup': self.enable_startup_var.get(),
            'enable_audio': self.enable_audio_var.get()
        }

        # Controlla la modalità di distribuzione scelta
        deployment_mode = self.deployment_mode_var.get()

        if deployment_mode == 'external':
            # Modalità esterna: genera l'exe e chiedi dove salvarlo
            if self.generate_external_executable(config):
                # Se l'operazione è riuscita, chiudi il dialog
                self.result = config
                self.root.quit()
                self.root.destroy()
            else:
                # Se l'operazione è fallita, non chiudere il dialog
                return
        else:
            # Modalità locale: procedi come prima
            # Ottieni la directory di configurazione
            config_dir = self.get_config_directory()

            try:
                # Salva la configurazione nella directory nascosta
                config_path = os.path.join(config_dir, 'config.json')
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)

                # Crea il file nopopup nella directory di configurazione
                nopopup_path = os.path.join(config_dir, 'nopopup.txt')
                with open(nopopup_path, 'w') as f:
                    f.write(f"Configurazione completata il {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("File creato per evitare il popup di configurazione")

                # Genera sempre l'eseguibile nella modalità locale
                if self.enable_startup_var.get():
                    # Genera l'eseguibile e configura l'avvio automatico (include anche l'avvio)
                    if not self.setup_startup_registry(config_dir):
                        return
                else:
                    # Genera l'eseguibile ma non configurare l'avvio automatico
                    exe_path = self.create_and_deploy_executable(config_dir)
                    if not exe_path:
                        messagebox.showerror(t['exe_creation_error'], t['exe_creation_error'])
                        return

                    # Se l'avvio automatico era abilitato prima, rimuovilo
                    if self.registry_manager.is_in_startup():
                        self.registry_manager.remove_from_startup()

                    # Mostra messaggio di successo per la creazione dell'eseguibile
                    messagebox.showinfo(t['exe_creation_success'],
                                      f"{t['exe_creation_success']}\n\nPercorso: {exe_path}")

                    # Avvia l'eseguibile generato (solo se non è stato avviato tramite setup_startup_registry)
                    self.start_generated_executable(exe_path, config_dir)

                # Crea il file riepilogativo sul desktop se richiesto
                if self.create_desktop_summary_var.get():
                    self.create_desktop_summary_file(config, config_dir)

            except Exception as e:
                messagebox.showerror(t['config_dir_error'], f"{t['config_dir_error']}: {str(e)}")
                return

            self.result = config
            messagebox.showinfo(t['config_saved'], t['config_saved_msg'])

            self.root.quit()
            self.root.destroy()
    
    def cancel(self):
        """Annulla la configurazione"""
        self.result = None
        self.root.quit()
        self.root.destroy()
    
    def show(self):
        """Mostra il dialog e restituisce il risultato"""
        # Gestisce la chiusura della finestra con la X
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        self.root.mainloop()
        return self.result


class ScreenRecorder:
    def __init__(self):
        # Controlla se è specificata una directory di configurazione personalizzata
        self.config_dir = self.get_config_directory()
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.nopopup_file = os.path.join(self.config_dir, "nopopup.txt")
        
        # Assicurati che la directory di configurazione esista
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Carica o crea la configurazione
        if not self.load_or_create_config():
            # Configurazione annullata, solleva un'eccezione per interrompere l'inizializzazione
            raise SystemExit("Configurazione annullata dall'utente")
        
        # Inizializza le variabili
        self.recording = False
        self.video_writer = None
        self.audio_frames = []
        self.audio_thread = None
        self.sequence_number = 1
        
        # Parametri video
        self.fps = 20
        self.screen_size = pyautogui.size()
        
        # Parametri audio (ora configurabili)
        self.sample_rate = 44100
        self.channels = 1
        self.audio_dtype = np.float32
        
        # Setup logging
        self.setup_logging()
        
        # Nascondi la finestra della console
        self.hide_console()
        
        # Assicurati che la directory esista
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.log_message("ScreenRecorder inizializzato correttamente")
        
        if self.config_dir != os.path.dirname(os.path.abspath(__file__)):
            self.log_message(f"Directory configurazione: {self.config_dir}")
    
    def get_config_directory(self):
        """Restituisce la directory per i file di configurazione"""
        # Controlla se è specificata una directory personalizzata tramite argomento
        if len(sys.argv) > 1 and sys.argv[1] == '--config-dir' and len(sys.argv) > 2:
            return sys.argv[2]

        # Controlla se siamo in un eseguibile PyInstaller con file incorporati
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Siamo in un eseguibile generato con PyInstaller
            # Verifica se esistono file di configurazione incorporati
            incorporated_config = os.path.join(sys._MEIPASS, 'config.json')
            incorporated_nopopup = os.path.join(sys._MEIPASS, 'nopopup.txt')

            if os.path.exists(incorporated_config) and os.path.exists(incorporated_nopopup):
                # Questo è un eseguibile portatile - deve auto-installarsi
                return self.auto_install_portable_executable(incorporated_config, incorporated_nopopup)

        # Directory predefinita nascosta nel sistema
        config_dir = os.path.join(os.environ['LOCALAPPDATA'], 'ScreenRecorderAuto')

        try:
            os.makedirs(config_dir, exist_ok=True)
        except Exception as e:
            print(f"Errore creazione directory configurazione: {e}")
            # Fallback alla directory corrente
            config_dir = os.path.dirname(os.path.abspath(__file__))

        return config_dir

    def auto_install_portable_executable(self, incorporated_config, incorporated_nopopup):
        """Auto-installa l'eseguibile portatile nel sistema"""
        try:
            # Directory di destinazione nell'LOCALAPPDATA
            target_config_dir = os.path.join(os.environ['LOCALAPPDATA'], 'ScreenRecorderAuto')
            os.makedirs(target_config_dir, exist_ok=True)

            # Copia i file di configurazione nella directory di destinazione
            target_config_file = os.path.join(target_config_dir, 'config.json')
            target_nopopup_file = os.path.join(target_config_dir, 'nopopup.txt')

            shutil.copy2(incorporated_config, target_config_file)
            shutil.copy2(incorporated_nopopup, target_nopopup_file)

            # Copia se stesso nella directory di destinazione
            current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
            target_exe = os.path.join(target_config_dir, 'ScreenRecorderAuto.exe')

            # Se l'eseguibile di destinazione non esiste o è diverso, copialo
            if not os.path.exists(target_exe) or not self.files_are_identical(current_exe, target_exe):
                shutil.copy2(current_exe, target_exe)
                print(f"Eseguibile copiato in: {target_exe}")

            # Carica la configurazione per determinare se abilitare l'avvio automatico
            with open(target_config_file, 'r') as f:
                config = json.load(f)

            # Se la configurazione include l'avvio automatico, configuralo
            if config.get('enable_startup', False):
                registry_manager = RegistryManager()
                startup_command = f'"{target_exe}" --config-dir "{target_config_dir}"'

                if not registry_manager.is_in_startup():
                    success = registry_manager.add_to_startup(startup_command)
                    if success:
                        print("Avvio automatico configurato con successo")
                    else:
                        print("Errore nella configurazione dell'avvio automatico")

            print(f"Auto-installazione completata. Directory di configurazione: {target_config_dir}")
            return target_config_dir

        except Exception as e:
            print(f"Errore durante l'auto-installazione: {e}")
            # In caso di errore, usa una directory temporanea come fallback
            temp_config_dir = os.path.join(os.environ['TEMP'], 'ScreenRecorderAuto_portable')
            os.makedirs(temp_config_dir, exist_ok=True)

            try:
                shutil.copy2(incorporated_config, temp_config_dir)
                shutil.copy2(incorporated_nopopup, temp_config_dir)
                return temp_config_dir
            except Exception as e2:
                print(f"Errore anche nel fallback: {e2}")
                return os.path.dirname(os.path.abspath(__file__))

    def files_are_identical(self, file1, file2):
        """Controlla se due file sono identici confrontando le dimensioni e la data di modifica"""
        try:
            if not os.path.exists(file1) or not os.path.exists(file2):
                return False

            stat1 = os.stat(file1)
            stat2 = os.stat(file2)

            return (stat1.st_size == stat2.st_size and
                   abs(stat1.st_mtime - stat2.st_mtime) < 2)  # Tolleranza di 2 secondi
        except Exception:
            return False

    def load_or_create_config(self):
        """Carica la configurazione esistente o ne crea una nuova"""
        if os.path.exists(self.nopopup_file):
            # Il file nopopup esiste, carica la configurazione
            self.load_config()
            return True
        else:
            # Prima volta, mostra il dialog di configurazione
            return self.show_configuration_dialog()
    
    def show_configuration_dialog(self):
        """Mostra il dialog di configurazione"""
        try:
            dialog = ConfigurationDialog()
            config = dialog.show()

            if config is None:
                # L'utente ha annullato, interrompi l'esecuzione
                print("Configurazione annullata. Il programma verrà chiuso.")
                return False
            else:
                # Applica la configurazione
                self.apply_config(config)
                return True

        except Exception as e:
            print(f"Errore durante la configurazione: {e}")
            return False
    
    def use_default_config(self):
        """Usa la configurazione predefinita"""
        default_config = {
            'output_dir': self.get_default_output_dir(),
            'segment_duration': 120,
            'audio_device_id': None,
            'audio_device_name': "Dispositivo predefinito",
            'enable_logging': True,
            'language': 'it',
            'enable_startup': False,
            'enable_audio': True
        }
        self.apply_config(default_config)
        
        # Salva la configurazione predefinita
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            
            # Crea il file nopopup per evitare il popup in futuro
            with open(self.nopopup_file, 'w') as f:
                f.write(f"Configurazione predefinita creata il {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Errore nel salvare la configurazione predefinita: {e}")
    
    def get_default_output_dir(self):
        """Restituisce la directory di output predefinita"""
        # Directory predefinita specifica richiesta dall'utente
        preferred_dir = os.path.join(os.path.expanduser("~"), "Documents", "Docs")
        
        try:
            # Crea la directory se non esiste
            os.makedirs(preferred_dir, exist_ok=True)
            # Testa se possiamo scrivere
            test_file = os.path.join(preferred_dir, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return preferred_dir
        except (PermissionError, OSError) as e:
            # Se per qualche motivo non riusciamo ad accedere, prova alternative
            fallback_dirs = [
                os.path.join(os.path.expanduser("~"), "Documents"),
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.expanduser("~")
            ]
            
            for fallback_dir in fallback_dirs:
                try:
                    os.makedirs(fallback_dir, exist_ok=True)
                    test_file = os.path.join(fallback_dir, "test_write.tmp")
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    return fallback_dir
                except (PermissionError, OSError):
                    continue
            
            # Se tutto fallisce, ritorna comunque la directory preferita
            return preferred_dir
    
    def load_config(self):
        """Carica la configurazione da file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                self.apply_config(config)
            else:
                self.use_default_config()
        except Exception as e:
            print(f"Errore nel caricare la configurazione: {e}")
            self.use_default_config()
    
    def apply_config(self, config):
        """Applica la configurazione caricata"""
        self.output_dir = config.get('output_dir', self.get_default_output_dir())
        self.segment_duration = config.get('segment_duration', 120)
        self.audio_device_id = config.get('audio_device_id', None)
        self.audio_device_name = config.get('audio_device_name', "Dispositivo predefinito")
        self.enable_logging = config.get('enable_logging', True)
        self.language = config.get('language', 'it')
        self.enable_startup = config.get('enable_startup', False)
        self.enable_audio = config.get('enable_audio', True)
    
    def setup_logging(self):
        """Configura il logging su file"""
        if self.enable_logging:
            log_path = os.path.join(self.output_dir, "recorder.log")
            try:
                logging.basicConfig(
                    filename=log_path,
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filemode='a'
                )
                self.logger = logging.getLogger(__name__)
                self.logger.info("=== Logging abilitato ===")
            except PermissionError:
                # Se non possiamo scrivere il log, usa la console
                logging.basicConfig(level=logging.INFO)
                self.logger = logging.getLogger(__name__)
                self.logger.info("Impossibile scrivere log su file, uso console")
        else:
            # Logging disabilitato, usa solo la console
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
            self.logger.info("Logging su file disabilitato")
    
    def hide_console(self):
        """Nasconde la finestra della console su Windows"""
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
        except Exception as e:
            self.log_message(f"Impossibile nascondere la console: {e}")
    
    def log_message(self, message):
        """Scrive i messaggi nel log"""
        if self.enable_logging:
            self.logger.info(message)
        else:
            # Se il logging è disabilitato, mostra solo nella console
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    
    def get_filename(self):
        """Genera il nome del file con formato giorno-mese-anno_ora-minuti-secondi"""
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        return timestamp
    
    def audio_callback(self, indata, frames, time, status):
        """Callback per la registrazione audio"""
        if status:
            self.log_message(f"Status audio: {status}")
        if self.recording:
            audio_data = indata.astype(self.audio_dtype)
            self.audio_frames.append(audio_data)
    
    def start_audio_recording(self):
        """Avvia la registrazione audio"""
        self.audio_frames = []
        try:
            # Usa il dispositivo audio configurato se specificato
            device = self.audio_device_id if self.audio_device_id is not None else None
            
            with sd.InputStream(callback=self.audio_callback, 
                              device=device,
                              channels=self.channels, 
                              samplerate=self.sample_rate,
                              dtype=self.audio_dtype,
                              blocksize=1024):
                self.log_message(f"Registrazione audio avviata - Dispositivo: {self.audio_device_name}")
                while self.recording:
                    time.sleep(0.1)
        except Exception as e:
            self.log_message(f"Errore registrazione audio: {e}")
    
    def save_audio(self, filename):
        """Salva l'audio registrato"""
        if not self.audio_frames:
            self.log_message("Nessun frame audio da salvare")
            return None
            
        try:
            audio_filename = f"{filename}_audio.wav"
            audio_path = os.path.join(self.output_dir, audio_filename)
            
            # Concatena tutti i frame audio
            audio_data = np.concatenate(self.audio_frames, axis=0)
            self.log_message(f"Frame audio concatenati: {len(self.audio_frames)}")
            
            # Normalizza l'audio
            if audio_data.max() > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Converti in int16 per il salvataggio WAV
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Salva come file WAV
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            
            self.log_message(f"Audio salvato: {audio_path}")
            return audio_path
            
        except Exception as e:
            self.log_message(f"Errore nel salvare l'audio: {e}")
            return None
    
    def combine_video_audio(self, video_path, audio_path, final_path):
        """Combina video e audio in un unico file"""
        try:
            self.log_message("Inizio combinazione video e audio...")
            
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            
            self.log_message(f"Durata video: {video_clip.duration}s")
            self.log_message(f"Durata audio: {audio_clip.duration}s")
            
            # Sincronizza la durata
            min_duration = min(video_clip.duration, audio_clip.duration)
            video_clip = video_clip.subclip(0, min_duration)
            audio_clip = audio_clip.subclip(0, min_duration)
            
            # Combina video e audio
            final_clip = video_clip.set_audio(audio_clip)
            
            # File temporaneo audio nella stessa directory di destinazione
            temp_audio_path = os.path.join(self.output_dir, 'temp-audio.m4a')
            
            # Scrivi il file finale
            final_clip.write_videofile(
                final_path, 
                codec='libx264', 
                audio_codec='aac',
                temp_audiofile=temp_audio_path,
                remove_temp=True,
                fps=self.fps,
                verbose=False,
                logger=None
            )
            
            # Chiudi i clip
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            # Rimuovi i file temporanei nella directory di destinazione
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
            except Exception as e:
                self.log_message(f"Avviso: Impossibile rimuovere file temporanei: {e}")
            
            self.log_message("Combinazione completata con successo")
            
        except Exception as e:
            self.log_message(f"Errore durante la combinazione: {e}")
            # Fallback: mantieni almeno il video nella directory di destinazione
            try:
                fallback_path = final_path.replace('.mp4', '_solo_video.avi')
                if os.path.exists(video_path):
                    os.rename(video_path, fallback_path)
                    self.log_message(f"Salvato solo video come: {fallback_path}")
            except Exception as e2:
                self.log_message(f"Errore anche nel fallback: {e2}")
    
    def record_segment(self):
        """Registra un singolo segmento"""
        filename = self.get_filename()
        video_filename = f"{filename}_video.avi"
        video_path = os.path.join(self.output_dir, video_filename)
        final_filename = f"{filename}.mp4"
        final_path = os.path.join(self.output_dir, final_filename)
        
        # Configura il codec video
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.video_writer = cv2.VideoWriter(video_path, fourcc, self.fps, self.screen_size)
        
        if not self.video_writer.isOpened():
            self.log_message("Errore: Impossibile aprire VideoWriter")
            return
        
        # Avvia la registrazione audio in un thread separato (solo se abilitata)
        self.recording = True
        if self.enable_audio:
            self.audio_thread = threading.Thread(target=self.start_audio_recording)
            self.audio_thread.start()
        else:
            self.audio_thread = None
        
        start_time = time.time()
        frame_count = 0
        next_frame_time = start_time
        
        self.log_message(f"Inizio registrazione segmento {self.sequence_number}: {filename}")
        self.log_message(f"Directory output: {self.output_dir}")
        
        # Registra per la durata specificata (ora configurabile)
        while time.time() - start_time < self.segment_duration:
            current_time = time.time()
            
            # Controlla se è ora di catturare il prossimo frame
            if current_time >= next_frame_time:
                try:
                    # Cattura lo schermo
                    screenshot = pyautogui.screenshot()
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Scrivi il frame
                    self.video_writer.write(frame)
                    frame_count += 1
                    
                    # Calcola quando catturare il prossimo frame
                    next_frame_time += 1.0 / self.fps
                    
                    # Se siamo in ritardo, non cercare di recuperare
                    if next_frame_time < current_time:
                        next_frame_time = current_time + 1.0 / self.fps
                        
                except Exception as e:
                    self.log_message(f"Errore cattura frame: {e}")
            else:
                # Piccola pausa per non sovraccaricare la CPU
                time.sleep(0.001)
        
        # Ferma la registrazione
        self.recording = False
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=5)
        self.video_writer.release()
        
        self.log_message(f"Frame totali registrati: {frame_count}")
        self.log_message(f"FPS effettivo: {frame_count / self.segment_duration:.2f}")
        
        # Salva l'audio solo se abilitato
        if self.enable_audio:
            audio_path = self.save_audio(filename)

            # Combina video e audio
            if audio_path and os.path.exists(audio_path):
                self.combine_video_audio(video_path, audio_path, final_path)
                self.log_message(f"Segmento completato: {final_filename}")
            else:
                # Se c'è stato un errore con l'audio, salva solo il video
                try:
                    os.rename(video_path, final_path.replace('.mp4', '.avi'))
                    self.log_message(f"Segmento completato (solo video): {final_filename.replace('.mp4', '.avi')}")
                except Exception as e:
                    self.log_message(f"Errore nel rinominare il file: {e}")
        else:
            # Audio disabilitato, salva solo il video
            try:
                os.rename(video_path, final_path.replace('.mp4', '.avi'))
                self.log_message(f"Segmento completato (solo video): {final_filename.replace('.mp4', '.avi')}")
            except Exception as e:
                self.log_message(f"Errore nel rinominare il file: {e}")
        
        self.sequence_number += 1
    
    def run(self):
        """Avvia la registrazione continua"""
        # Messaggi multilingua per il logging
        messages = {
            'it': {
                'start': "Avvio registrazione continua dello schermo...",
                'output_dir': "Directory di output:",
                'config_dir': "Directory di configurazione:",
                'resolution': "Risoluzione:",
                'fps': "FPS:",
                'segment_duration': "Durata segmenti:",
                'audio_device': "Dispositivo audio:",
                'logging_enabled': "Logging abilitato:",
                'language': "Lingua:",
                'seconds': "secondi",
                'yes': "Sì",
                'no': "No",
                'interrupted': "Registrazione interrotta dall'utente",
                'error': "Errore durante la registrazione:"
            },
            'en': {
                'start': "Starting continuous screen recording...",
                'output_dir': "Output directory:",
                'config_dir': "Configuration directory:",
                'resolution': "Resolution:",
                'fps': "FPS:",
                'segment_duration': "Segment duration:",
                'audio_device': "Audio device:",
                'logging_enabled': "Logging enabled:",
                'language': "Language:",
                'seconds': "seconds",
                'yes': "Yes",
                'no': "No",
                'interrupted': "Recording interrupted by user",
                'error': "Error during recording:"
            }
        }
        
        lang = getattr(self, 'language', 'it')
        m = messages.get(lang, messages['it'])
        
        self.log_message(m['start'])
        self.log_message(f"{m['config_dir']} {self.config_dir}")
        self.log_message(f"{m['output_dir']} {self.output_dir}")
        self.log_message(f"{m['resolution']} {self.screen_size}")
        self.log_message(f"{m['fps']} {self.fps}")
        self.log_message(f"{m['segment_duration']} {self.segment_duration} {m['seconds']}")
        self.log_message(f"{m['audio_device']} {self.audio_device_name}")
        self.log_message(f"{m['logging_enabled']} {m['yes'] if self.enable_logging else m['no']}")
        self.log_message(f"{m['language']} {lang}")
        
        try:
            while True:
                self.record_segment()
        except KeyboardInterrupt:
            self.log_message(m['interrupted'])
        except Exception as e:
            self.log_message(f"{m['error']} {e}")
        finally:
            if self.video_writer:
                self.video_writer.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        recorder = ScreenRecorder()
        recorder.run()
    except SystemExit as e:
        # Uscita controllata (configurazione annullata)
        print(str(e))
        sys.exit(0)
    except Exception as e:
        print(f"Errore durante l'avvio: {e}")
        input("Premi Enter per chiudere...")  # Per vedere l'errore prima che la finestra si chiuda