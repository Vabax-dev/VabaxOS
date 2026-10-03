"""VabaxOS Update - Sistema di aggiornamenti accessibile con sintesi vocale.

Gestisce aggiornamenti di:
- Pacchetti Debian (APT)
- Pacchetti VabaxOS dal repository ufficiale
- Applicazioni Flatpak

Fornisce:
- Interfaccia grafica (GTK 4)
- Modalità CLI con sintesi vocale
- Notifiche accessibili
- Changelog leggibili
- Progress vocale durante l'installazione
"""

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class UpdatePriority(Enum):
    """Priorità di un aggiornamento."""
    SECURITY = "security"
    IMPORTANT = "important"
    BUGFIX = "bugfix"
    FEATURE = "feature"
    UPDATE = "update"


class UpdateSource(Enum):
    """Fonte di un aggiornamento."""
    DEBIAN = "debian"
    VABAXOS = "vabaxos"
    FLATPAK = "flatpak"


@dataclass
class Update:
    """Rappresenta un aggiornamento disponibile."""
    name: str
    current_version: str
    new_version: str
    priority: UpdatePriority
    source: UpdateSource
    size: int  # bytes
    changelog: str
    description: str
    is_security: bool = False
    requires_reboot: bool = False


class UpdateManager:
    """Gestisce il controllo e l'installazione degli aggiornamenti."""

    def __init__(self):
        self.available_updates: List[Update] = []
        self.last_check: Optional[datetime] = None

    def check_updates(self, use_cache=True):
        """Controlla gli aggiornamenti disponibili.

        Args:
            use_cache: Se True, usa la cache APT esistente senza update

        Returns:
            Lista di aggiornamenti disponibili
        """
        self.available_updates = []

        # Controlla pacchetti Debian/VabaxOS
        apt_updates = self._check_apt_updates(use_cache)
        self.available_updates.extend(apt_updates)

        # Controlla Flatpak (se installato)
        flatpak_updates = self._check_flatpak_updates()
        self.available_updates.extend(flatpak_updates)

        self.last_check = datetime.now()
        return self.available_updates

    def _check_apt_updates(self, use_cache=True):
        """Controlla aggiornamenti APT."""
        updates = []

        try:
            # Se non usiamo la cache, aggiorniamo
            if not use_cache:
                subprocess.run(
                    ["apt-get", "update"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )

            # Simula controllo aggiornamenti (in un sistema reale useremmo python-apt)
            # Per ora creiamo dati di esempio
            result = subprocess.run(
                ["apt-get", "--just-print", "upgrade"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                # Parsing semplificato dell'output
                for line in result.stdout.split('\n'):
                    if line.startswith('Inst '):
                        # Formato: Inst PACKAGE [OLD] (NEW ...)
                        parts = line.split()
                        if len(parts) >= 4:
                            name = parts[1]
                            current = parts[2].strip('[]')
                            new = parts[3].strip('()')

                            # Determina fonte e priorità
                            source = UpdateSource.VABAXOS if name.startswith('vabaxos-') else UpdateSource.DEBIAN
                            priority = self._determine_priority(name, line)
                            is_security = 'security' in line.lower() or 'Debian-Security' in line
                            requires_reboot = name in ['linux-image', 'systemd', 'dbus']

                            updates.append(Update(
                                name=name,
                                current_version=current,
                                new_version=new,
                                priority=priority,
                                source=source,
                                size=self._estimate_size(name),
                                changelog=self._get_changelog(name, new),
                                description=self._get_description(name),
                                is_security=is_security,
                                requires_reboot=requires_reboot
                            ))

        except Exception as e:
            print(f"Errore durante il controllo APT: {e}")

        return updates

    def _check_flatpak_updates(self):
        """Controlla aggiornamenti Flatpak."""
        updates = []

        try:
            result = subprocess.run(
                ["flatpak", "remote-ls", "--updates", "--columns=application,version"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        app_id = parts[0]
                        version = parts[1]

                        updates.append(Update(
                            name=app_id,
                            current_version="installed",
                            new_version=version,
                            priority=UpdatePriority.UPDATE,
                            source=UpdateSource.FLATPAK,
                            size=10 * 1024 * 1024,  # Stima
                            changelog="Aggiornamento Flatpak",
                            description=self._get_flatpak_description(app_id),
                            is_security=False,
                            requires_reboot=False
                        ))

        except FileNotFoundError:
            # Flatpak non installato
            pass
        except Exception as e:
            print(f"Errore durante il controllo Flatpak: {e}")

        return updates

    def _determine_priority(self, package_name, output_line):
        """Determina la priorità di un aggiornamento."""
        if 'security' in output_line.lower():
            return UpdatePriority.SECURITY

        # Pacchetti critici
        critical = ['linux-image', 'systemd', 'gnome-shell', 'orca', 'speech-dispatcher']
        if any(pkg in package_name for pkg in critical):
            return UpdatePriority.IMPORTANT

        # Pacchetti VabaxOS
        if package_name.startswith('vabaxos-'):
            return UpdatePriority.BUGFIX

        return UpdatePriority.UPDATE

    def _estimate_size(self, package_name):
        """Stima la dimensione di un pacchetto."""
        # In un sistema reale useremmo python-apt
        # Per ora stime ragionevoli
        if 'linux-image' in package_name:
            return 50 * 1024 * 1024  # 50 MB
        elif 'gnome' in package_name:
            return 10 * 1024 * 1024  # 10 MB
        elif package_name.startswith('vabaxos-'):
            return 500 * 1024  # 500 KB
        return 1 * 1024 * 1024  # 1 MB default

    def _get_changelog(self, package_name, version):
        """Ottiene il changelog di un pacchetto."""
        # In un sistema reale leggeremmo il changelog da APT
        # Per ora placeholder
        return f"Aggiornamento a versione {version}"

    def _get_description(self, package_name):
        """Ottiene la descrizione di un pacchetto."""
        descriptions = {
            'orca': 'Lettore di schermo per GNOME',
            'speech-dispatcher': 'Sistema di sintesi vocale',
            'gnome-shell': 'Interfaccia desktop GNOME',
            'linux-image': 'Kernel Linux',
        }

        for key, desc in descriptions.items():
            if key in package_name:
                return desc

        if package_name.startswith('vabaxos-'):
            return 'Componente VabaxOS'

        return 'Pacchetto Debian'

    def _get_flatpak_description(self, app_id):
        """Ottiene la descrizione di un'app Flatpak."""
        return f"Applicazione {app_id.split('.')[-1]}"

    def get_summary(self):
        """Restituisce un riepilogo degli aggiornamenti."""
        total = len(self.available_updates)
        security = sum(1 for u in self.available_updates if u.is_security)
        important = sum(1 for u in self.available_updates if u.priority == UpdatePriority.IMPORTANT)
        total_size = sum(u.size for u in self.available_updates)

        return {
            'total': total,
            'security': security,
            'important': important,
            'total_size': total_size,
            'requires_reboot': any(u.requires_reboot for u in self.available_updates)
        }

    def get_speech_summary(self):
        """Restituisce un riepilogo leggibile a voce."""
        summary = self.get_summary()

        if summary['total'] == 0:
            return "Nessun aggiornamento disponibile. Il sistema è aggiornato."

        text = f"{summary['total']} "
        text += "aggiornamento disponibile. " if summary['total'] == 1 else "aggiornamenti disponibili. "

        if summary['security'] > 0:
            text += f"{summary['security']} di sicurezza. "

        if summary['important'] > 0:
            text += f"{summary['important']} importante. " if summary['important'] == 1 else f"{summary['important']} importanti. "

        # Dimensione totale
        size_mb = summary['total_size'] / (1024 * 1024)
        if size_mb < 1:
            text += f"Dimensione: {summary['total_size'] / 1024:.0f} kilobyte. "
        else:
            text += f"Dimensione: {size_mb:.1f} megabyte. "

        if summary['requires_reboot']:
            text += "Richiede riavvio. "

        return text

    def install_updates(self, updates: List[Update], progress_callback=None):
        """Installa gli aggiornamenti selezionati.

        Args:
            updates: Lista di Update da installare
            progress_callback: Funzione chiamata per ogni pacchetto (name, current, total)

        Returns:
            (success, message)
        """
        if not updates:
            return True, "Nessun aggiornamento da installare"

        # Separa per fonte
        apt_updates = [u for u in updates if u.source in (UpdateSource.DEBIAN, UpdateSource.VABAXOS)]
        flatpak_updates = [u for u in updates if u.source == UpdateSource.FLATPAK]

        success = True
        messages = []

        # Installa aggiornamenti APT
        if apt_updates:
            apt_success, apt_msg = self._install_apt_updates(apt_updates, progress_callback)
            success = success and apt_success
            messages.append(apt_msg)

        # Installa aggiornamenti Flatpak
        if flatpak_updates:
            flatpak_success, flatpak_msg = self._install_flatpak_updates(flatpak_updates, progress_callback)
            success = success and flatpak_success
            messages.append(flatpak_msg)

        return success, " ".join(messages)

    def _install_apt_updates(self, updates, progress_callback):
        """Installa aggiornamenti APT."""
        total = len(updates)

        try:
            for i, update in enumerate(updates, 1):
                if progress_callback:
                    progress_callback(update.name, i, total)

                # In un sistema reale useremmo python-apt
                # Per ora simuliamo
                result = subprocess.run(
                    ["apt-get", "install", "-y", f"{update.name}={update.new_version}"],
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode != 0:
                    return False, f"Errore durante l'installazione di {update.name}"

            return True, f"{total} pacchetti installati con successo"

        except Exception as e:
            return False, f"Errore: {e}"

    def _install_flatpak_updates(self, updates, progress_callback):
        """Installa aggiornamenti Flatpak."""
        total = len(updates)

        try:
            for i, update in enumerate(updates, 1):
                if progress_callback:
                    progress_callback(update.name, i, total)

                result = subprocess.run(
                    ["flatpak", "update", "-y", update.name],
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode != 0:
                    return False, f"Errore durante l'aggiornamento di {update.name}"

            return True, f"{total} applicazioni Flatpak aggiornate"

        except Exception as e:
            return False, f"Errore: {e}"


def format_size(bytes_size):
    """Formatta una dimensione in byte in formato leggibile."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"


def speak(text, wait=False):
    """Legge un testo con la sintesi vocale.

    Args:
        text: Testo da leggere
        wait: Se True, attende la fine della lettura
    """
    try:
        args = ["spd-say"]
        if wait:
            args.append("-w")
        args.extend(["-r", "10", text])

        subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        pass
