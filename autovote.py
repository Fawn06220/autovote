import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import time, threading, os, subprocess, webbrowser, socket
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import traceback
import psutil

# Vars
profile_flag = os.path.join(os.path.dirname(__file__), "FlowerProfileReady.flag")
brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
user_data_dir = os.path.join(os.getenv("LOCALAPPDATA"), "BraveSoftware", "Brave-Browser", "User Data")
profile_dir = "FlowerPower"
port_arg = "--remote-debugging-port=9222"




def wait_for_debug_port(host="localhost", port=9222, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                print("🟢 Port 9222 prêt.")
                return True
        except OSError:
            time.sleep(0.3)
    print("⛔ Timeout : port 9222 non disponible.")
    return False

def launch_brave_debug_if_needed():
    def detect_conflicting_brave_instances():
        found_good = False
        print("\n🧪 Analyse des processus Brave principaux...\n")
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info['name']
                cmdline_list = proc.info['cmdline']
                if not cmdline_list or not isinstance(cmdline_list, list):
                    continue
                cmdline = " ".join(cmdline_list).lower()
                if name and "brave" in name.lower():
                    print(f"🔎 PID {proc.pid} | CMD: {cmdline}")
                    if any(arg.startswith("--type=") for arg in cmdline_list):
                        continue
                    is_flower = "--profile-directory=flowerpower" in cmdline
                    has_debug = "--remote-debugging-port=9222" in cmdline
                    if is_flower and has_debug:
                        print("✅ Bonne instance Brave détectée.")
                        found_good = True
                    else:
                        print("❌ Conflit : Brave lancé avec mauvais profil ou sans port debug.")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False if found_good else False

    if detect_conflicting_brave_instances():
        messagebox.showerror("Brave déjà ouvert",
            "❌ Brave est déjà ouvert avec un autre profil.\n\n"
            "Veuillez fermer toutes les fenêtres Brave avant de démarrer le vote.")
        raise RuntimeError("Brave conflict: autre instance active")

    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] and "brave" in proc.info['name'].lower():
                cmd = " ".join(proc.info['cmdline'])
                if "FlowerPower" in cmd and port_arg in cmd:
                    print("✅ Brave FlowerPower déjà lancé avec port 9222")
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and "brave" in proc.info['name'].lower():
                if any("FlowerPower" in arg for arg in proc.info['cmdline']):
                    print(f"🛑 Fermeture résiduelle de Brave FlowerPower (PID {proc.pid})")
                    proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    time.sleep(2)
    print("🚀 Lancement de Brave FlowerPower en mode debug")
    subprocess.Popen([
        brave_path,
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={profile_dir}",
        "--remote-debugging-port=9222",
        "--no-first-run",
        "--no-default-browser-check"
    ])

    if not wait_for_debug_port():
        raise RuntimeError("Brave ne répond pas sur le port 9222")
    
def show_profile_ready_popup(parent=None):
    confirmed = {"value": False}

    def on_confirm():
        confirmed["value"] = True
        with open(profile_flag, "w") as f:
                f.write("ready")
                print("✅ Connexion validée.")
        if spin_job["id"]:
            try:
                popup.after_cancel(spin_job["id"])
            except:
                pass
        popup.destroy()

    def disable_close():
        pass  # empêche fermeture avec X ou Alt+F4

    popup = tk.Toplevel(parent) if parent else tk.Toplevel()
    popup.title("Etapes Essentielles !")
    popup.configure(bg="black")
    popup.resizable(False, False)
    popup.protocol("WM_DELETE_WINDOW", disable_close)
    popup.attributes("-topmost", True)

    # Dimensions finales
    final_w, final_h = 450, 460
    screen_w = popup.winfo_screenwidth()
    screen_h = popup.winfo_screenheight()
    x = (screen_w // 2) - (final_w // 2)
    y = (screen_h // 2) - (final_h // 2)

    # Commence petit
    popup.geometry(f"50x50+{x}+{y}")
    popup.update()


    style = ttk.Style(popup)
    style.configure("Modern.TButton", font=("Segoe UI", 10, "bold"),
                    foreground="#000000", background="#3A3A3A",
                    borderwidth=0, padding=10)
    style.map("Modern.TButton", background=[("active", "#5A5A5A")])

    container = tk.Frame(popup, bg="black")
    container.pack(expand=True)

    logo_path = os.path.join(os.path.dirname(__file__), "img/logo_fleur.png")
    if os.path.exists(logo_path):
        img = Image.open(logo_path).resize((64, 64))
        photo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(container, image=photo, bg="black")
        logo_label.image = photo
        logo_label.pack(pady=10)
        popup.iconphoto(True, photo)

        # Variables attachées à popup
        popup.logo_img_original = img
        popup.logo_label = logo_label
        
        spin_job = {"id": None}
        
        def animate_fade_spin_grow(step=0, total_steps=40):
            t = step / total_steps

            # Interpolation progressive
            scale = t
            alpha = min(1.0, t)

            w = int(final_w * scale)
            h = int(final_h * scale)
            dx = (final_w - w) // 2
            dy = (final_h - h) // 2
            popup.geometry(f"{w}x{h}+{x + dx}+{y + dy}")
            popup.wm_attributes("-alpha", alpha)

            if step < total_steps:
                popup.after(16, animate_fade_spin_grow, step + 1, total_steps)

        def spin_logo(angle=0):
            if not popup.winfo_exists():
                return
            if hasattr(popup, "logo_img_original") and hasattr(popup, "logo_label"):
                rotated = popup.logo_img_original.rotate(angle, resample=Image.BICUBIC)
                rotated_photo = ImageTk.PhotoImage(rotated)
                popup.logo_label.configure(image=rotated_photo)
                popup.logo_label.image = rotated_photo
                spin_job["id"] = popup.after(40, spin_logo, (angle + 3) % 360)

        animate_fade_spin_grow()
        spin_logo()


    important_lbl = tk.Label(
        container,
        text="Important : Veuillez en premier lieu installer le navigateur Brave si vous ne le possédez pas !",
        bg="black",
        fg="yellow",
        font=("Helvetica", 10, "bold"),
        wraplength=400,
        justify="center"
    )
    important_lbl.pack(pady=(0, 8))

    dl_btn = ttk.Button(
        container,
        text="Télécharger Brave",
        command=lambda: webbrowser.open("https://brave.com/fr/download/"),
        style="Modern.TButton"
    )
    dl_btn.pack(pady=(0, 12))
    
    brave_done_lbl = tk.Label(
    container,
    text="Une fois Brave installé cliquez ici !",
    bg="black",
    fg="yellow",
    font=("Segoe UI", 9, "bold"),
    wraplength=400,
    justify="center"
    )
    brave_done_lbl.pack(pady=(0, 6))

    brave_installed_btn = ttk.Button(
    container,
    text="Brave Installé",
    command=ensure_flower_power_profile,
    style="Modern.TButton"
    )
    brave_installed_btn.pack(pady=(0, 20))


    message = tk.Label(
        container,
        text="Veuillez créer un compte ou vous connecter\nsur le site KingPet (dans Brave).\n\nUne fois terminé, cliquez sur le bouton ci-dessous.",
        font=("Segoe UI", 10),
        fg="yellow",
        bg="black",
        justify="center",
        wraplength=420
    )
    message.pack(pady=(0, 20))

    ok_btn = ttk.Button(container, text="J’ai terminé", command=on_confirm, style="Modern.TButton")
    ok_btn.pack()

    popup.grab_set()
    if parent:
        parent.wait_window(popup)
    else:
        popup.mainloop()

    return confirmed["value"]

def ensure_flower_power_profile():
    url_vote = "https://www.kingpet.fr/vote/flower437"
    if not os.path.exists(profile_flag):
        subprocess.Popen([
            brave_path,
            f"--user-data-dir={user_data_dir}",
            f"--profile-directory={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            url_vote
        ])
        time.sleep(2)

class AutoVoteApp:
    def __init__(self, root):
        print("🟡 AutoVoteApp init START")
        self.root = root
        self.root.title("Flower AutoVote Brave Only")
        self.root.geometry("500x300")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        icon_path = os.path.join(os.path.dirname(__file__), "img/logo_fleur.png")
        if os.path.exists(icon_path):
            icon_img = Image.open(icon_path)
            self.icon_photo = ImageTk.PhotoImage(icon_img)
            root.iconphoto(True, self.icon_photo)

        root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.count = 0
        self.start_time = None
        self.running = False
        self.stop_event = threading.Event()

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
        self.label = tk.Label(root, text="", font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="black")

        self.canvas.create_window(5, 5, anchor="nw", window=self.start_btn)
        self.root.after_idle(self.place_widgets)
        print("🟢 AutoVoteApp init END")

    def place_widgets(self):
        spacing = 2
        bottom_margin = 5
        left_margin = 5

        height_start = self.start_btn.winfo_reqheight()
        y_stop = 5 + height_start + spacing

        self.canvas.create_window(5, y_stop, anchor="nw", window=self.stop_btn)
        self.canvas.create_window(left_margin, 300 - bottom_margin, anchor="sw", window=self.label)

    def start_vote(self):
        try:
            self.running = True
            self.stop_event.clear()
            self.start_btn.state(["disabled"])
            self.stop_btn.state(["!disabled"])
            launch_brave_debug_if_needed()

            self.options = Options()
            self.options.debugger_address = "localhost:9222"
            self.driver_path = os.path.join("driver", "chromedriver.exe")
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
        print("🛑 Demande d'arrêt du vote reçue.")
        self.running = False
        self.stop_event.set()
        self.start_btn.state(["!disabled"])
        self.stop_btn.state(["disabled"])
        self.label.config(text=f"Prochain vote dans : 0 min 0 sec - Total : {self.count}")

    def vote_thread(self):
        if self.running:
            print("🧵 Lancement d’un thread de vote")
            threading.Thread(target=self.vote_action, daemon=True).start()

    def vote_action(self):
        try:
            if self.stop_event.is_set():
                return

            self.driver.execute_script("window.open('');")
            time.sleep(1)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get("https://www.kingpet.fr/vote/flower437")

            WebDriverWait(self.driver, 10).until(
                EC.url_contains("kingpet.fr/vote/flower437"))
            print("🌐 Page de vote confirmée")

            if self.stop_event.is_set():
                return

            btn_vote = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.ID, "vote-btn")))
            btn_vote.click()

            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'restants')]")))
                print("⏳ Vote déjà effectué (restants détecté)")
                self.start_time = time.time()
                self.update_timer()
                self.root.after(600_000, self.vote_thread)
                return
            except:
                pass

            if self.stop_event.is_set():
                return

            bouton = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gratuit')]")))
            bouton.click()

            self.start_time = time.time()
            if self.count == 0:
                self.update_timer()
            self.root.after(605_000, self.vote_thread)
            self.count += 1
            self.driver.refresh()
            time.sleep(1)
            self.driver.close()
            if self.driver.window_handles:
                self.driver.switch_to.window(self.driver.window_handles[0])

        except Exception as e:
            print(f"⛔ Erreur dans vote_action : {e}")

    def update_timer(self):
        if self.running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            remaining = max(0, 600 - elapsed)
            m, s = divmod(remaining, 60)
            self.label.config(text=f"Prochain vote dans : {m} min {s} sec - Total : {self.count}")
            self.root.after(1000, self.update_timer)

    def on_closing(self):
        self.stop_vote()
        self.root.destroy()

if __name__ == "__main__":
    print("📦 Lancement de l’application...")
    root = tk.Tk()
    root.withdraw()
    if not os.path.exists(profile_flag):
        show_profile_ready_popup(parent=root)
    root.deiconify()
    app = AutoVoteApp(root)
    root.mainloop()
