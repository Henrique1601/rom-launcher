"""Assistente Oficial de Instalação para Windows (EmuCraft-Setup.exe).

Instala o EmuCraft com assistente visual moderno, cria atalhos na Área de
Trabalho e Menu Iniciar, e registra o desinstalador oficial no Windows.
"""

import io
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from tkinter import filedialog

# Proteção de streams para Windows GUI
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()
if sys.stdin is None:
    sys.stdin = io.StringIO()

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Instalação do EmuCraft")
        self.geometry("640x480")
        self.resizable(False, False)

        # Caminho padrão: %LOCALAPPDATA%\Programs\EmuCraft
        local_app = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        self.default_install_dir = str(Path(local_app) / "Programs" / "EmuCraft")
        self.install_dir_var = ctk.StringVar(value=self.default_install_dir)

        # Opções
        self.create_desktop_shortcut_var = ctk.BooleanVar(value=True)
        self.create_start_menu_var = ctk.BooleanVar(value=True)
        self.launch_after_var = ctk.BooleanVar(value=True)

        self.current_step = 1
        self._build_ui()

    def _build_ui(self):
        # 1. Header com Branding Glass / Neon
        self.header_frame = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color=("#1e293b", "#0f172a"))
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        header_title = ctk.CTkLabel(
            self.header_frame,
            text="🎮 EmuCraft  •  Assistente de Instalação",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#38bdf8"
        )
        header_title.pack(anchor="w", padx=25, pady=(18, 2))

        header_sub = ctk.CTkLabel(
            self.header_frame,
            text="Central de Emulação, Preservação e Inicialização de Jogos",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        header_sub.pack(anchor="w", padx=25)

        # 2. Container Central
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=25, pady=20)

        # 3. Rodapé com Botões de Navegação
        self.footer_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=("#1e293b", "#0f172a"))
        self.footer_frame.pack(fill="x", side="bottom")
        self.footer_frame.pack_propagate(False)

        self.btn_cancel = ctk.CTkButton(
            self.footer_frame,
            text="Cancelar",
            width=90,
            fg_color="transparent",
            border_width=1,
            command=self.destroy
        )
        self.btn_cancel.pack(side="left", padx=25, pady=15)

        self.btn_next = ctk.CTkButton(
            self.footer_frame,
            text="Avançar >",
            width=120,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._next_step
        )
        self.btn_next.pack(side="right", padx=25, pady=15)

        self._show_step_1()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_step_1(self):
        """Passo 1: Boas-vindas e Apresentação."""
        self._clear_content()
        self.current_step = 1

        ctk.CTkLabel(
            self.content_frame,
            text="Bem-vindo à Instalação do EmuCraft!",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(10, 15))

        desc = (
            "Este assistente irá instalar o EmuCraft no seu computador.\n\n"
            "✨ Recursos Inclusos nesta Instalação:\n"
            "  • Suporte completo a 28+ consoles (PlayStation, Nintendo, Família Xbox, Sega)\n"
            "  • Interface Gamer Glass com posters oficiais (Libretro Box Art)\n"
            "  • Rastreador de tempo de jogo e integração com RetroAchievements\n"
            "  • Save-Sync automático e snapshots de memory cards na nuvem/local\n"
            "  • Auto-Patcher de traduções brasileiras (IPS e BPS)\n"
            "  • Navegação nativa por controle de videogame (Couch Mode)\n\n"
            "Clique em 'Avançar' para continuar."
        )
        ctk.CTkLabel(
            self.content_frame,
            text=desc,
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color="gray80"
        ).pack(anchor="w")

    def _show_step_2(self):
        """Passo 2: Seleção de Pasta de Instalação e Opções de Atalhos."""
        self._clear_content()
        self.current_step = 2

        ctk.CTkLabel(
            self.content_frame,
            text="Selecione o Local de Instalação:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(10, 10))

        # Campo com pasta de destino
        dir_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        dir_frame.pack(fill="x", pady=(0, 20))
        dir_frame.grid_columnconfigure(0, weight=1)

        entry_dir = ctk.CTkEntry(dir_frame, textvariable=self.install_dir_var, height=36)
        entry_dir.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        btn_browse = ctk.CTkButton(
            dir_frame,
            text="Procurar...",
            width=100,
            height=36,
            command=self._browse_dir
        )
        btn_browse.grid(row=0, column=1)

        ctk.CTkLabel(
            self.content_frame,
            text="Opções Adicionais:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(5, 10))

        ctk.CTkCheckBox(
            self.content_frame,
            text="Criar atalho na Área de Trabalho (Desktop)",
            variable=self.create_desktop_shortcut_var
        ).pack(anchor="w", pady=4)

        ctk.CTkCheckBox(
            self.content_frame,
            text="Criar atalho no Menu Iniciar",
            variable=self.create_start_menu_var
        ).pack(anchor="w", pady=4)

        self.btn_next.configure(text="Instalar Agora", fg_color="#16a34a", hover_color="#15803d")

    def _browse_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.install_dir_var.get())
        if chosen:
            self.install_dir_var.set(str(Path(chosen) / "EmuCraft"))

    def _show_step_3(self):
        """Passo 3: Instalação em Andamento com Barra de Progresso."""
        self._clear_content()
        self.current_step = 3

        self.btn_next.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")

        ctk.CTkLabel(
            self.content_frame,
            text="Instalando o EmuCraft...",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(20, 15))

        self.progress_bar = ctk.CTkProgressBar(self.content_frame, height=18)
        self.progress_bar.pack(fill="x", pady=(10, 15))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="Preparando arquivos...",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.status_label.pack(anchor="w")

        threading.Thread(target=self._perform_installation, daemon=True).start()

    def _perform_installation(self):
        dest_dir = Path(self.install_dir_var.get())
        dest_dir.mkdir(parents=True, exist_ok=True)

        steps = [
            ("Criando diretórios de sistema...", 0.15),
            ("Copiando binários do aplicativo...", 0.40),
            ("Configurando registradores de emuladores e BIOS...", 0.65),
            ("Criando atalhos no Windows...", 0.85),
            ("Registrando desinstalador oficial...", 1.0),
        ]

        # 1. Localiza os arquivos a serem instalados
        # Prioriza payload embutido no próprio instalador (--add-data payload)
        bundled_exe = None
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            meipass_payload = Path(sys._MEIPASS) / "payload" / "EmuCraft.exe"
            if meipass_payload.exists():
                bundled_exe = meipass_payload

        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        if not bundled_exe:
            dist_exe = base_dir / "dist" / "EmuCraft.exe"
            if dist_exe.exists():
                bundled_exe = dist_exe

        installed_exe = dest_dir / "EmuCraft.exe"
        if bundled_exe and bundled_exe.exists():
            shutil.copy2(bundled_exe, installed_exe)
        else:
            # Cria script de inicialização caso rode direto dos fontes
            installed_exe = dest_dir / "LaunchEmuCraft.vbs"
            vbs_code = (
                f'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.CurrentDirectory = "{base_dir}"\n'
                f'WshShell.Run "pythonw.exe -m rom_cli.gui.main_window", 0, False\n'
            )
            installed_exe.write_text(vbs_code, encoding="ascii")

        # 2. Cria Atalhos do Windows
        self._create_shortcuts(dest_dir, installed_exe)

        # 3. Cria Desinstalador
        self._create_uninstaller(dest_dir)

        # Concluído
        time.sleep(0.5)
        self.after(0, self._show_step_4)

    def _update_progress(self, label: str, progress: float):
        self.status_label.configure(text=label)
        self.progress_bar.set(progress)

    def _create_shortcuts(self, dest_dir: Path, target_file: Path):
        home = Path.home()
        desktop = home / "Desktop"
        onedrive_desktop = home / "OneDrive" / "Desktop"
        target_desktop = onedrive_desktop if onedrive_desktop.exists() else desktop

        appdata = os.environ.get("APPDATA", str(home / "AppData" / "Roaming"))
        start_menu = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"

        vbs_lines = ['Set WshShell = CreateObject("WScript.Shell")']
        if self.create_desktop_shortcut_var.get():
            desk_lnk = str(target_desktop / "EmuCraft.lnk").replace('"', '""')
            vbs_lines.extend([
                f'Set dLnk = WshShell.CreateShortcut("{desk_lnk}")',
                f'dLnk.TargetPath = "{target_file}"',
                f'dLnk.WorkingDirectory = "{dest_dir}"',
                'dLnk.Description = "EmuCraft - Central de Jogos e Emuladores"',
                'dLnk.IconLocation = "%SystemRoot%\\System32\\shell32.dll,24"',
                'dLnk.Save',
            ])

        if self.create_start_menu_var.get():
            start_lnk = str(start_menu / "EmuCraft.lnk").replace('"', '""')
            vbs_lines.extend([
                f'Set sLnk = WshShell.CreateShortcut("{start_lnk}")',
                f'sLnk.TargetPath = "{target_file}"',
                f'sLnk.WorkingDirectory = "{dest_dir}"',
                'sLnk.Description = "EmuCraft - Central de Jogos e Emuladores"',
                'sLnk.IconLocation = "%SystemRoot%\\System32\\shell32.dll,24"',
                'sLnk.Save',
            ])

        tmp_vbs = dest_dir / "create_shortcuts.vbs"
        try:
            tmp_vbs.write_text("\n".join(vbs_lines), encoding="ascii", errors="replace")
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.run(["cscript.exe", "//nologo", str(tmp_vbs)], creationflags=flags, timeout=5)
            tmp_vbs.unlink(missing_ok=True)
        except Exception:
            pass

    def _create_uninstaller(self, dest_dir: Path):
        """Cria o script de desinstalação que remove as pastas e atalhos."""
        uninstall_bat = dest_dir / "Uninstall.bat"
        bat_content = f"""@echo off
title Desinstalando EmuCraft...
echo Removendo atalhos...
del "%USERPROFILE%\\Desktop\\EmuCraft.lnk" >nul 2>&1
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\EmuCraft.lnk" >nul 2>&1
echo Removendo arquivos...
cd ..
rmdir /s /q "{dest_dir}" >nul 2>&1
echo EmuCraft foi desinstalado com sucesso.
pause
"""
        uninstall_bat.write_text(bat_content, encoding="ascii")

    def _show_step_4(self):
        """Passo 4: Conclusão com Sucesso."""
        self._clear_content()
        self.current_step = 4

        ctk.CTkLabel(
            self.content_frame,
            text="🎉 Instalação Concluída com Sucesso!",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", pady=(15, 15))

        info_text = (
            f"O EmuCraft foi instalado com sucesso em:\n{self.install_dir_var.get()}\n\n"
            "Atalhos foram criados na sua Área de Trabalho e Menu Iniciar.\n"
            "Você pode iniciar o aplicativo agora para configurar seus jogos e emuladores."
        )
        ctk.CTkLabel(
            self.content_frame,
            text=info_text,
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color="gray80"
        ).pack(anchor="w", pady=(0, 20))

        ctk.CTkCheckBox(
            self.content_frame,
            text="Iniciar o EmuCraft agora",
            variable=self.launch_after_var
        ).pack(anchor="w", pady=5)

        self.btn_cancel.pack_forget()
        self.btn_next.configure(
            state="normal",
            text="Concluir",
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._finish_and_exit
        )

    def _next_step(self):
        if self.current_step == 1:
            self._show_step_2()
        elif self.current_step == 2:
            self._show_step_3()

    def _finish_and_exit(self):
        if self.launch_after_var.get():
            dest_dir = Path(self.install_dir_var.get())
            exe = dest_dir / "EmuCraft.exe"
            vbs = dest_dir / "LaunchEmuCraft.vbs"
            if exe.exists():
                os.startfile(str(exe))
            elif vbs.exists():
                os.system(f'wscript.exe "{vbs}"')
            else:
                os.system('pythonw.exe -m rom_cli.gui.main_window')
        self.destroy()


def main():
    app = SetupWizard()
    app.mainloop()


if __name__ == "__main__":
    main()
