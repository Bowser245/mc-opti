import minecraft_launcher_lib
import subprocess
import uuid
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import threading
import psutil
import os
import shutil
import zipfile
# --- CONFIGURATION INITIALE ---
minecraft_directory = os.path.join(os.getenv('APPDATA'), ".minecraft_custom")
chemin_skin_selectionne = None

def get_default_ram():
    # Calcule 75% de la RAM totale du PC en Go
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    return round(total_ram_gb * 0.75)

def charger_versions():
    # Récupère toutes les versions (Release + Snapshots)
    try:
        versions = minecraft_launcher_lib.utils.get_version_list()
        return [v['id'] for v in versions]
    except:
        return ["1.20.1"]
def activer_mode_performance():
    pass

def restaurer_mode_normal():
    pass
def log(message):
    """Ajoute un message dans la console visuelle"""
    text_log.config(state="normal")
    text_log.insert(tk.END, f"> {message}\n")
    text_log.see(tk.END)
    text_log.config(state="disabled")

def update_progress(current, total, status):
    """Met à jour la barre de progression"""
    progress_bar["maximum"] = total
    progress_bar["value"] = current
    root.update_idletasks()
def choisir_skin():
    global chemin_skin_selectionne
    # Ouvre le sélecteur de fichiers de Kubuntu
    fichier = filedialog.askopenfilename(
        title="Sélectionne ton skin (.png)",
        filetypes=[("Images PNG", "*.png")]
    )
    if fichier:
        chemin_skin_selectionne = fichier
        label_skin_nom.config(text=os.path.basename(fichier), fg="#a6e3a1")
        log(f"Skin sélectionné : {os.path.basename(fichier)}")

def appliquer_skin_local(minecraft_dir):
    """Crée le Resource Pack avec le fichier choisi"""
    if not chemin_skin_selectionne:
        return

    rp_dir = os.path.join(minecraft_dir, "resourcepacks", "SkinPerso")
    skin_dest_dir = os.path.join(rp_dir, "assets", "minecraft", "textures", "entity")

    try:
        os.makedirs(skin_dest_dir, exist_ok=True)
        # On copie le fichier choisi vers le pack en le renommant steve.png et alex.png
        #67 67 67
        shutil.copy(chemin_skin_selectionne, os.path.join(skin_dest_dir, "steve.png"))

        shutil.copy(chemin_skin_selectionne, os.path.join(skin_dest_dir, "alex.png"))

        with open(os.path.join(rp_dir, "pack.mcmeta"), "w") as f:
            f.write('{"pack": {"pack_format": 15, "description": "Skin Local Launcher"}}')
        log("Resource Pack du skin mis à jour.")
        log("Pack de skin généré. N'oublie pas de l'activer dans Options > Resource Packs !")
    except Exception as e:
        log(f"Erreur skin : {e}")
def lancer_jeu():
    username = entry_pseudo.get()
    version_selectionnee = combo_version.get()
    ram_max = entry_ram.get()

    if not username:
        messagebox.showwarning("Erreur", "Entre un pseudo !")
        return

    btn_jouer.config(state="disabled", text="Lancement...")
    log(f"Initialisation pour {username}...")

    def process():
        try:
            # Callbacks pour lier la bibliothèque à l'interface
            appliquer_skin_local(minecraft_directory)
            callback = {
                "setStatus": lambda text: log(text),
                "setProgress": lambda value: update_progress(value, progress_bar["maximum"], label_status["text"]),
                "setMax": lambda value: update_progress(progress_bar["value"], value, label_status["text"])
            }

            # Installation avec barre de progression
            log(f"Vérification des fichiers ({version_selectionnee})...")
            minecraft_launcher_lib.install.install_minecraft_version(version_selectionnee, minecraft_directory, callback=callback)

            options = {
                "username": username,
                "uuid": str(uuid.uuid4()),
                "token": "0",
                "executablePath": "javaw.exe",
                "jvmArguments": [f"-Xmx{ram_max}G", f"-Xms{ram_max}G", "-XX:+UseG1GC"]
            }

            activer_mode_performance()
            log("Démarrage de Minecraft...")
            command = minecraft_launcher_lib.command.get_minecraft_command(version_selectionnee, minecraft_directory, options)

            # Cacher la fenêtre pendant le jeu pour libérer des ressources

            subprocess.call(command, creationflags=subprocess.CREATE_NO_WINDOW)

            restaurer_mode_normal()
            log("Jeu fermé avec succès.")
        except Exception as e:
            log(f"ERREUR : {str(e)}")
            messagebox.showerror("Erreur", str(e))
            restaurer_mode_normal()
        finally:
            btn_jouer.config(state="normal", text="JOUER")
            progress_bar["value"] = 0
            label_status.config(text="Prêt")

    threading.Thread(target=process).start()
# --- AJOUT DU RACCOURCI CLAVIER ---
# On "bind" la séquence de touches sur la fenêtre principale
# Note : Tkinter gère mieux les combinaisons simples,
# pour faire "Esc+X+K" on va utiliser une astuce de séquence.
from pynput import keyboard

# --- FONCTION DE KILL ---
def kill_minecraft():
    try:
        # Commande radicale pour Windows (/f = forcer, /im = image name)
        subprocess.run("taskkill /f /im javaw.exe", check=False, shell=True)
        current_keys.clear()
        root.after(0, root.deiconify)
        log("!!! LE JEU A ÉTÉ ARRÊTÉ SUR WINDOWS !!!")
    except Exception as e:
        print(f"Erreur Windows Taskkill: {e}")
# --- GESTION DU RACCOURCI GLOBAL (Esc + X + K) ---
# On utilise un "Set" pour vérifier si les touches sont pressées en même temps
current_keys = set()

def on_press(key):
    try:
        # On ajoute la touche pressée au set
        if key == keyboard.Key.esc:
            current_keys.add('esc')
        elif hasattr(key, 'char'):
            current_keys.add(key.char.lower())

        # VERIFICATION DE LA COMBINAISON : Esc + X + K
        if all(k in current_keys for k in ['esc', 'x', 'k']):
            kill_minecraft()

    except Exception:
        pass

def on_release(key):
    try:
        # On retire la touche quand elle est relâchée
        if key == keyboard.Key.esc:
            current_keys.remove('esc')
        elif hasattr(key, 'char'):
            current_keys.remove(key.char.lower())
    except KeyError:
        pass

# --- LANCEMENT DE L'ÉCOUTEUR ---
# On le lance dans un thread séparé pour ne pas bloquer l'interface Tkinter
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
# Note : Il faut appuyer sur Echap, puis X, puis K rapidement.
# --- INTERFACE ---
root = tk.Tk()
root.title("Windows Minecraft Launcher")
root.geometry("500x700") # Un peu plus grand pour les logs
root.configure(bg="#1e1e2e")
style = ttk.Style()
style.theme_use('clam')

tk.Label(root, text="MINECRAFT OFFLINE", fg="#f38ba8", bg="#1e1e2e", font=("Arial", 18, "bold")).pack(pady=15)

# Pseudo
tk.Label(root, text="Pseudo :", fg="white", bg="#1e1e2e").pack()
entry_pseudo = tk.Entry(root, font=("Arial", 12), justify="center", bg="#313244", fg="white", insertbackground="white")
entry_pseudo.pack(pady=5)

# Versions
tk.Label(root, text="Version :", fg="white", bg="#1e1e2e").pack(pady=5)
combo_version = ttk.Combobox(root, values=charger_versions(), state="readonly", width=25)
combo_version.set("1.20.1")
combo_version.pack(pady=5)

# RAM
tk.Label(root, text="RAM autorisée (Go) :", fg="white", bg="#1e1e2e").pack(pady=5)
entry_ram = tk.Entry(root, font=("Arial", 12), justify="center", width=10, bg="#313244", fg="white", insertbackground="white")
entry_ram.insert(0, str(get_default_ram()))
entry_ram.pack(pady=5)

# --- NOUVEAUX ÉLÉMENTS : PROGRESSION ET LOGS ---
label_status = tk.Label(root, text="Prêt", fg="#a6adc8", bg="#1e1e2e")
label_status.pack(pady=(10, 0))

progress_bar = ttk.Progressbar(root, orient="horizontal", length=350, mode="determinate")
progress_bar.pack(pady=5)

tk.Label(root, text="Console :", fg="white", bg="#1e1e2e").pack()
text_log = tk.Text(root, height=10, width=55, bg="#11111b", fg="#a6e3a1", font=("Courier", 8), state="disabled")
text_log.pack(pady=5, padx=10)
# Section Skin
frame_skin = tk.Frame(root, bg="#1e1e2e")
frame_skin.pack(pady=10)

btn_skin = tk.Button(frame_skin, text="Choisir Skin (.png)", command=choisir_skin, bg="#89b4fa", fg="#1e1e2e", font=("Arial", 10))
btn_skin.pack(side=tk.LEFT, padx=5)

label_skin_nom = tk.Label(frame_skin, text="Aucun skin", fg="#fab387", bg="#1e1e2e", font=("Arial", 9))
label_skin_nom.pack(side=tk.LEFT)
# Bouton Jouer
btn_jouer = tk.Button(root, text="JOUER", command=lancer_jeu, bg="#a6e3a1", fg="#1e1e2e", font=("Arial", 12, "bold"), width=20)
btn_jouer.pack(pady=20)
# Version et édition
vee = tk.Label(root, text="Windows, V1.1", fg="#fab387", bg="#1e1e2e", font=("Arial", 9))
vee.pack()
root.mainloop()
