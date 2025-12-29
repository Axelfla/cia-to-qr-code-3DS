import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import qrcode
from PIL import Image, ImageTk
import os
import requests
from bs4 import BeautifulSoup
import webbrowser

class QRCodeGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("3DS QR Code Generator - Multi-serveur")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a2e")
        
        self.games = []
        self.filtered_games = []
        self.selected_game = None
        self.qr_image = None
        
        # URLs de serveurs prédéfinis
        self.preset_servers = {
            "Internet Archive - 3DS CIAs": "https://archive.org/download/nintendo3dscias",
            "Internet Archive - 3DS Complete": "https://archive.org/download/3ds-complete-collection",
            "Internet Archive - No-Intro": "https://archive.org/download/no-intro_20200517",
            "Personnalisé": ""
        }
        
        self.current_url = self.preset_servers["Internet Archive - 3DS CIAs"]
        
        # Créer l'interface
        self.create_widgets()
    
    def load_from_server(self):
        """Charge la liste depuis le serveur configuré"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Attention", "Veuillez entrer une URL valide")
            return
        
        self.current_url = url
        self.status_label.config(text=f"Chargement depuis {url}...")
        self.root.update()
        
        try:
            # Récupérer la page
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trouver tous les liens de fichiers de jeux
            self.games = []
            links = soup.find_all('a', href=True)
            
            # Extensions de fichiers supportées
            valid_extensions = ['.cia', '.3ds', '.3dsx', '.zip', '.7z', '.rar']
            
            for link in links:
                href = link.get('href', '')
                
                # Vérifier si c'est un fichier de jeu
                if any(href.lower().endswith(ext) for ext in valid_extensions):
                    # Nettoyer le nom
                    name = os.path.basename(href)
                    original_name = name
                    
                    # Enlever l'extension
                    for ext in valid_extensions:
                        if name.lower().endswith(ext):
                            name = name[:-len(ext)]
                            break
                    
                    name = name.replace('_', ' ').replace('-', ' ')
                    
                    # URL complète de téléchargement
                    if href.startswith('http'):
                        download_url = href
                    else:
                        download_url = f"{url.rstrip('/')}/{href.lstrip('/')}"
                    
                    # Extraire des infos du nom
                    region = 'Unknown'
                    if any(x in name.upper() for x in ['(USA)', '[USA]', 'USA']):
                        region = 'USA'
                    elif any(x in name.upper() for x in ['(EUR)', '[EUR]', 'EUROPE', 'EUR']):
                        region = 'EUR'
                    elif any(x in name.upper() for x in ['(JPN)', '[JPN]', 'JAPAN', 'JPN']):
                        region = 'JPN'
                    
                    # Type de fichier
                    file_type = original_name.split('.')[-1].upper()
                    
                    self.games.append({
                        'id': str(len(self.games)),
                        'name': name.strip(),
                        'region': region,
                        'download_url': download_url,
                        'filename': original_name,
                        'type': file_type
                    })
            
            if len(self.games) == 0:
                messagebox.showwarning("Attention", f"Aucun fichier de jeu trouvé sur:\n{url}")
                self.status_label.config(text="❌ Aucun jeu trouvé")
            else:
                # Trier par nom
                self.games.sort(key=lambda x: x['name'])
                self.filtered_games = self.games[:100]
                self.update_game_list()
                self.status_label.config(text=f"✅ {len(self.games)} jeux chargés depuis le serveur")
                messagebox.showinfo("Succès", f"{len(self.games)} jeux chargés avec succès !")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erreur réseau", f"Impossible de se connecter au serveur:\n{str(e)}\n\nVérifiez l'URL et votre connexion internet.")
            self.status_label.config(text="❌ Erreur de connexion")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement:\n{str(e)}")
            self.status_label.config(text="❌ Erreur de chargement")
    
    def on_server_select(self, event):
        """Gère la sélection d'un serveur prédéfini"""
        selected = self.server_combo.get()
        
        if selected == "Personnalisé":
            self.url_entry.config(state="normal")
            self.url_entry.delete(0, tk.END)
            self.url_entry.focus()
        else:
            url = self.preset_servers.get(selected, "")
            self.url_entry.config(state="normal")
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
    
    def create_widgets(self):
        """Crée l'interface graphique"""
        # Titre
        title = tk.Label(
            self.root,
            text="3DS QR Code Generator - Multi-serveur",
            font=("Arial", 22, "bold"),
            bg="#1a1a2e",
            fg="#00d4ff"
        )
        title.pack(pady=10)
        
        subtitle = tk.Label(
            self.root,
            text="Générez des QR codes pour télécharger depuis n'importe quel serveur",
            font=("Arial", 10),
            bg="#1a1a2e",
            fg="#a8dadc"
        )
        subtitle.pack()
        
        # Frame de configuration du serveur
        server_frame = tk.LabelFrame(
            self.root,
            text="⚙️ Configuration du serveur",
            font=("Arial", 11, "bold"),
            bg="#16213e",
            fg="white",
            relief="ridge",
            bd=2
        )
        server_frame.pack(pady=10, padx=20, fill="x")
        
        # Serveurs prédéfinis
        preset_frame = tk.Frame(server_frame, bg="#16213e")
        preset_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(
            preset_frame,
            text="Serveurs prédéfinis:",
            font=("Arial", 10),
            bg="#16213e",
            fg="white"
        ).pack(side="left", padx=5)
        
        self.server_combo = ttk.Combobox(
            preset_frame,
            values=list(self.preset_servers.keys()),
            state="readonly",
            font=("Arial", 10),
            width=40
        )
        self.server_combo.set("Internet Archive - 3DS CIAs")
        self.server_combo.pack(side="left", padx=5)
        self.server_combo.bind('<<ComboboxSelected>>', self.on_server_select)
        
        # Barre URL personnalisée
        url_frame = tk.Frame(server_frame, bg="#16213e")
        url_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(
            url_frame,
            text="🌐 URL du serveur:",
            font=("Arial", 10),
            bg="#16213e",
            fg="white"
        ).pack(side="left", padx=5)
        
        self.url_entry = tk.Entry(
            url_frame,
            font=("Arial", 10),
            bg="#0f3460",
            fg="white",
            insertbackground="white",
            relief="flat",
            width=60
        )
        self.url_entry.insert(0, self.preset_servers["Internet Archive - 3DS CIAs"])
        self.url_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Boutons d'action
        action_frame = tk.Frame(server_frame, bg="#16213e")
        action_frame.pack(pady=10, padx=10)
        
        tk.Button(
            action_frame,
            text="🔄 Charger les jeux",
            command=self.load_from_server,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            action_frame,
            text="📋 Exemples d'URLs",
            command=self.show_url_examples,
            bg="#3498db",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=8
        ).pack(side="left", padx=5)
        
        # Barre de recherche
        search_frame = tk.Frame(self.root, bg="#1a1a2e")
        search_frame.pack(pady=10, padx=20, fill="x")
        
        search_label = tk.Label(
            search_frame,
            text="🔍 Rechercher:",
            font=("Arial", 12),
            bg="#1a1a2e",
            fg="white"
        )
        search_label.pack(side="left", padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 12),
            bg="#16213e",
            fg="white",
            insertbackground="white",
            relief="flat",
            width=50
        )
        search_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Liste des jeux (gauche)
        list_frame = tk.Frame(main_frame, bg="#16213e", relief="ridge", bd=2)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        list_title = tk.Label(
            list_frame,
            text="📦 Jeux disponibles",
            font=("Arial", 14, "bold"),
            bg="#16213e",
            fg="white"
        )
        list_title.pack(pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.game_listbox = tk.Listbox(
            list_frame,
            font=("Arial", 10),
            bg="#0f3460",
            fg="white",
            selectbackground="#6c5ce7",
            selectforeground="white",
            yscrollcommand=scrollbar.set,
            relief="flat"
        )
        self.game_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.game_listbox.bind('<<ListboxSelect>>', self.on_game_select)
        
        scrollbar.config(command=self.game_listbox.yview)
        
        # Panneau QR Code (droite)
        qr_frame = tk.Frame(main_frame, bg="#16213e", relief="ridge", bd=2)
        qr_frame.pack(side="right", fill="both", expand=True)
        
        self.qr_title = tk.Label(
            qr_frame,
            text="Chargez un serveur",
            font=("Arial", 13, "bold"),
            bg="#16213e",
            fg="white",
            wraplength=380
        )
        self.qr_title.pack(pady=10)
        
        self.info_label = tk.Label(
            qr_frame,
            text="Sélectionnez un serveur et cliquez sur 'Charger les jeux'",
            font=("Arial", 9),
            bg="#16213e",
            fg="#a8dadc",
            justify="center",
            wraplength=380
        )
        self.info_label.pack(pady=5)
        
        # Canvas pour le QR code
        self.qr_canvas = tk.Canvas(
            qr_frame,
            width=350,
            height=350,
            bg="white",
            relief="flat"
        )
        self.qr_canvas.pack(pady=10)
        
        # Boutons d'action
        btn_container = tk.Frame(qr_frame, bg="#16213e")
        btn_container.pack(pady=10)
        
        self.save_btn = tk.Button(
            btn_container,
            text="💾 Sauvegarder QR Code",
            command=self.save_qr_code,
            bg="#6c5ce7",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10,
            state="disabled"
        )
        self.save_btn.pack(pady=5)
        
        self.browser_btn = tk.Button(
            btn_container,
            text="🌐 Ouvrir dans le navigateur",
            command=self.open_in_browser,
            bg="#e67e22",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10,
            state="disabled"
        )
        self.browser_btn.pack(pady=5)
        
        # Info FBI
        info = tk.Label(
            qr_frame,
            text="📱 Scannez ce QR code avec FBI sur votre 3DS\npour télécharger le jeu directement",
            font=("Arial", 9),
            bg="#16213e",
            fg="#a8dadc",
            justify="center"
        )
        info.pack(pady=10)
        
        # Barre de statut
        self.status_label = tk.Label(
            self.root,
            text="Prêt - Sélectionnez un serveur et chargez les jeux",
            font=("Arial", 10),
            bg="#0f3460",
            fg="white",
            anchor="w"
        )
        self.status_label.pack(side="bottom", fill="x", padx=5, pady=5)
    
    def show_url_examples(self):
        """Affiche des exemples d'URLs"""
        examples = """
Exemples d'URLs de serveurs compatibles:

📦 Internet Archive:
• https://archive.org/download/nintendo3dscias
• https://archive.org/download/3ds-complete-collection
• https://archive.org/download/no-intro_20200517

🌐 Serveurs HTTP personnalisés:
• http://votre-serveur.com/roms/3ds/
• https://mon-nas.local/games/3ds/

💡 Conseils:
- L'URL doit pointer vers un répertoire contenant des fichiers
- Formats supportés: .cia, .3ds, .3dsx, .zip, .7z, .rar
- Le serveur doit permettre le listage des fichiers (directory listing)
        """
        
        messagebox.showinfo("Exemples d'URLs", examples)
    
    def update_game_list(self):
        """Met à jour la liste des jeux"""
        self.game_listbox.delete(0, tk.END)
        
        for game in self.filtered_games:
            display = f"{game['name']}"
            if game['region'] != 'Unknown':
                display += f" [{game['region']}]"
            display += f" ({game['type']})"
            self.game_listbox.insert(tk.END, display)
    
    def on_search(self, *args):
        """Filtre les jeux selon la recherche"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.filtered_games = self.games[:100]
        else:
            self.filtered_games = [
                game for game in self.games
                if search_term in game['name'].lower() or
                   search_term in game['region'].lower() or
                   search_term in game['type'].lower()
            ][:100]
        
        self.update_game_list()
        self.status_label.config(text=f"🔍 {len(self.filtered_games)} jeu(x) trouvé(s)")
    
    def on_game_select(self, event):
        """Gère la sélection d'un jeu"""
        selection = self.game_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        self.selected_game = self.filtered_games[index]
        
        # Mettre à jour les infos
        self.qr_title.config(text=self.selected_game['name'])
        
        info_text = f"Type: {self.selected_game['type']}\n"
        info_text += f"Région: {self.selected_game['region']}\n"
        info_text += f"Fichier: {self.selected_game['filename']}\n\n"
        info_text += f"URL: {self.selected_game['download_url']}"
        
        self.info_label.config(text=info_text)
        
        # Générer le QR code avec l'URL de téléchargement
        self.generate_qr_code()
        
        # Activer les boutons
        self.save_btn.config(state="normal")
        self.browser_btn.config(state="normal")
    
    def generate_qr_code(self):
        """Génère le QR code avec l'URL du serveur"""
        if not self.selected_game:
            return
        
        # Créer le QR code avec l'URL de téléchargement
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.selected_game['download_url'])
        qr.make(fit=True)
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((350, 350), Image.Resampling.LANCZOS)
        
        # Convertir pour Tkinter
        self.qr_image = ImageTk.PhotoImage(img)
        
        # Afficher sur le canvas
        self.qr_canvas.delete("all")
        self.qr_canvas.create_image(175, 175, image=self.qr_image)
    
    def save_qr_code(self):
        """Sauvegarde le QR code en PNG"""
        if not self.selected_game:
            return
        
        # Nettoyer le nom du fichier
        safe_name = "".join(c for c in self.selected_game['name'] if c.isalnum() or c in (' ', '-', '_'))
        default_name = f"{safe_name}_QR.png"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            # Créer le QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.selected_game['download_url'])
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(filename)
            
            messagebox.showinfo("✅ Succès", f"QR Code sauvegardé:\n{filename}")
    
    def open_in_browser(self):
        """Ouvre le lien dans le navigateur"""
        if self.selected_game:
            webbrowser.open(self.selected_game['download_url'])

if __name__ == "__main__":
    root = tk.Tk()
    app = QRCodeGenerator(root)
    root.mainloop()