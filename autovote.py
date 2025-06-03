import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import time, threading, os, subprocess, webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import sys
import traceback
import psutil

def launch_brave_debug_if_needed():
    brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    user_data_dir = os.path.join(os.getenv("LOCALAPPDATA"), "BraveSoftware", "Brave-Browser", "User Data")
    flower_profile = os.path.join(user_data_dir, "FlowerPower")

    # Vérifier si Brave est déjà lancé avec le bon port
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] and "brave" in proc.info['name'].lower():
                if any("--remote-debugging-port=9222" in arg for arg in proc.info['cmdline']):
                    print("✅ Brave déjà lancé avec port 9222")
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sinon, lancer Brave avec profil et port
    print("🚀 Lancement de Brave en mode debug (port 9222)")
    subprocess.Popen([
        brave_path,
        f'--user-data-dir={flower_profile}',
        '--remote-debugging-port=9222',
        '--no-first-run',
        '--no-default-browser-check'
    ])

    # Attendre que Brave ouvre le port
    time.sleep(3)


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = "".join(traceback.format_exception(ex_cls, ex, tb))
    print("⛔ Exception non interceptée :\n" + text)

sys.excepthook = log_uncaught_exceptions


def show_profile_ready_popup():
    confirmed = {"value": False}

    def on_confirm():
        confirmed["value"] = True
        popup.destroy()

    def disable_close():
        pass  # empêche fermeture avec X ou Alt+F4

    popup = tk.Tk()
    popup.title("Connexion requise")
    popup.geometry("400x250")
    popup.configure(bg="black")
    popup.resizable(False, False)
    popup.protocol("WM_DELETE_WINDOW", disable_close)

    style = ttk.Style(popup)
    style.configure("Modern.TButton", font=("Segoe UI", 10, "bold"),
                    foreground="#000000", background="#3A3A3A",
                    borderwidth=0, padding=10)
    style.map("Modern.TButton", background=[("active", "#5A5A5A")])

    logo_path = os.path.join(os.path.dirname(__file__), "img/logo_fleur.png")
    if os.path.exists(logo_path):
        img = Image.open(logo_path).resize((64, 64))
        photo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(popup, image=photo, bg="black")
        logo_label.image = photo
        logo_label.pack(pady=(10, 5))

    message = tk.Label(
        popup,
        text="Veuillez créer un compte ou vous connecter\nsur le site KingPet (dans Brave).\n\nUne fois terminé, cliquez sur le bouton ci-dessous.",
        font=("Segoe UI", 10),
        fg="white",
        bg="black",
        justify="center"
    )
    message.pack(pady=10)

    ok_btn = ttk.Button(popup, text="J’ai terminé", command=on_confirm, style="Modern.TButton")
    ok_btn.pack(pady=(0, 10))

    popup.eval('tk::PlaceWindow . center')
    popup.mainloop()

    return confirmed["value"]

def ensure_flower_power_profile():
    user_data = os.path.join(os.getenv("LOCALAPPDATA"), "BraveSoftware", "Brave-Browser", "User Data")
    flower_profile_path = os.path.join(user_data, "FlowerPower")
    profile_flag = os.path.join(os.path.dirname(__file__), "FlowerProfileReady.flag")
    brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    url_vote = "https://www.kingpet.fr/vote/flower437"

    if not os.path.exists(flower_profile_path):
        batch_path = os.path.join(os.path.dirname(__file__), "launch_flower_power.bat")
        if os.path.exists(batch_path):
            subprocess.call(['cmd.exe', '/c', batch_path])
        else:
            print("❌ Script batch introuvable.")

    if not os.path.exists(profile_flag):
        subprocess.Popen([
            brave_path,
            f"--user-data-dir={user_data}",
            "--profile-directory=FlowerPower",
            url_vote
        ])
        if show_profile_ready_popup():
            with open(profile_flag, "w") as f:
                f.write("ready")
            print("✅ Connexion validée.")
        else:
            print("❌ Connexion non confirmée. L’application ne démarre pas.")
            exit(0)
    else:
        print("✅ Connexion utilisateur déjà validée.")

class AutoVoteApp:
    def __init__(self, root):
        print("🟡 AutoVoteApp init START")
        self.root = root
        self.root.title("Flower AutoVote Brave Only")
        self.root.geometry("500x300")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        icon_path = os.path.join(os.path.dirname(__file__), "logo_fleur.png")
        if os.path.exists(icon_path):
            icon_img = Image.open(icon_path)
            self.icon_photo = ImageTk.PhotoImage(icon_img)
            root.iconphoto(True, self.icon_photo)

        root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.count = 0
        self.start_time = None
        self.running = False

        bg_path = os.path.join(os.getcwd(), "img/Fond.jpg")
        self.bg_photo = None
        if os.path.exists(bg_path):
            self.bg_image = Image.open(bg_path).resize((500, 300))
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)

        self.canvas = tk.Canvas(root, width=500, height=300, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        if self.bg_photo:
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        self.style = ttk.Style()
        self.style.configure("Modern.TButton", font=("Segoe UI", 10, "bold"),
                             foreground="#000000", background="#3A3A3A", borderwidth=0, padding=8)
        self.style.map("Modern.TButton", background=[("active", "#5A5A5A")])

        self.start_btn = ttk.Button(root, text="▶ Start", command=self.start_vote, style="Modern.TButton")
        self.stop_btn = ttk.Button(root, text="■ Stop", command=self.stop_vote, style="Modern.TButton")
        self.stop_btn.state(["disabled"])
        self.download_btn = ttk.Button(root, text="DL Brave", command=self.open_brave_website, style="Modern.TButton")
        self.label = tk.Label(root, text="", font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="black")

        self.canvas.create_window(5, 5, anchor="nw", window=self.start_btn)
        self.canvas.create_window(495, 5, anchor="ne", window=self.download_btn)
        self.root.after_idle(self.place_widgets)
        print("🟢 AutoVoteApp init END")

    def place_widgets(self):
        spacing = 2
        bottom_margin = 5
        left_margin = 5
        right_margin = 5

        height_start = self.start_btn.winfo_reqheight()
        y_stop = 5 + height_start + spacing

        self.canvas.create_window(5, y_stop, anchor="nw", window=self.stop_btn)
        self.canvas.create_window(left_margin, 300 - bottom_margin, anchor="sw", window=self.label)

    def open_brave_website(self):
        webbrowser.open("https://brave.com/fr/download/")



    def start_vote(self):
        try:
            self.running = True
            self.start_btn.state(["disabled"])
            self.stop_btn.state(["!disabled"])

            brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
            self.driver_path = os.path.join("driver", "chromedriver.exe")

            launch_brave_debug_if_needed()

            self.options = Options()
            self.options.debugger_address = "localhost:9222"

            service = Service(self.driver_path)
            self.driver = webdriver.Chrome(service=service, options=self.options)

            print("🚀 Connexion réussie à Brave existant")
            self.vote_thread()

        except Exception as e:
            traceback.print_exc()
            self.running = False
            self.start_btn.state(["!disabled"])
            self.stop_btn.state(["disabled"])
            messagebox.showerror("Erreur", f"Le vote n’a pas pu démarrer :\n{str(e) or 'Erreur inconnue'}")




    def stop_vote(self):
        self.running = False
        self.start_btn.state(["!disabled"])
        self.stop_btn.state(["disabled"])
        self.label.config(text=f"0H 0Min 0sec | Nb={self.count}")
        print("🛑 Vote arrêté : Brave reste ouvert, session utilisateur intacte.")

    def vote_thread(self):
        if self.running:
            print("🧵 Lancement d’un thread de vote")
            threading.Thread(target=self.vote_action, daemon=True).start()
            self.root.after(600_000, self.vote_thread)

    def vote_action(self):
        try:
            print("🔁 Démarrage vote_action()")
            print("🪟 Fenêtres :", self.driver.window_handles)
            self.driver.switch_to.window(self.driver.window_handles[0])

            print("🌐 URL active :", self.driver.current_url)
            if "kingpet" not in self.driver.current_url:
                print("🌐 Navigation vers la page de vote...")
                self.driver.get("https://www.kingpet.fr/vote/flower437")

            try:
                btn_vote = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "vote-btn"))
                )
                btn_vote.click()
                print("✅ Bouton de vote cliqué")
            except Exception as e:
                print(f"❌ Bouton de vote introuvable ou non cliquable : {e}")
                return

            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'restants')]"))
                )
                print("⏳ Vote déjà effectué (restants détecté)")
                return
            except:
                print("🔎 Aucun 'restants' détecté, on continue...")

            try:
                xpath = "//span[contains(text(), 'Gratuit')]"
                bouton = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                bouton.click()
                print("✅ Bouton 'Gratuit' cliqué")
                if self.count == 0:
                    self.start_time = time.time()
                    self.update_timer()
                self.count += 1
            except Exception as e:
                print(f"❌ Erreur clic 'Gratuit' : {e}")

        except Exception as e:
            print(f"⛔ Erreur générale dans vote_action() : {e}")



    def update_timer(self):
        if self.running:
            elapsed = int(time.time() - self.start_time)
            h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            self.label.config(text=f"{h}H {m}Min {s}sec | Nb={self.count}")
            self.root.after(1000, self.update_timer)

    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    print("📦 Lancement de l’application...")
    ensure_flower_power_profile()
    root = tk.Tk()
    app = AutoVoteApp(root)
    root.mainloop()
