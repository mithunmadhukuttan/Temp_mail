import requests
import customtkinter as ctk
from tkinter import messagebox
import threading
import time
import pyperclip

# Set Temp-Mail API URL and Headers
TEMP_MAIL_API = "https://api.mail.tm"

# Function to register and generate a temporary email
def generate_temp_email():
    try:
        # Fetch valid domains
        domains_response = requests.get(f"{TEMP_MAIL_API}/domains")
        if domains_response.status_code == 200:
            valid_domains = domains_response.json()["hydra:member"]
            if valid_domains:
                selected_domain = valid_domains[0]["domain"]  # Use the first available domain

                # Generate a random account
                random_email = f"user{int(time.time())}@{selected_domain}"
                response = requests.post(f"{TEMP_MAIL_API}/accounts", json={
                    "address": random_email,
                    "password": "password123"
                })

                if response.status_code == 201:
                    account = response.json()
                    return account['id'], account['address'], "password123"
                elif response.status_code == 409:
                    # Email already exists; fetch token
                    auth_response = requests.post(f"{TEMP_MAIL_API}/token", json={
                        "address": random_email,
                        "password": "password123"
                    })
                    if auth_response.status_code == 200:
                        account = auth_response.json()
                        return account['id'], account['address'], "password123"
                else:
                    print("Error generating email address:", response.text)
                    return None, None, None
            else:
                print("No valid domains available")
                return None, None, None
        else:
            print("Failed to fetch valid domains")
            return None, None, None
    except Exception as e:
        print("Exception generating email:", e)
        return None, None, None

# Function to get the token for API authentication
def get_token(email, password):
    try:
        response = requests.post(f"{TEMP_MAIL_API}/token", json={"address": email, "password": password})
        if response.status_code == 200:
            return response.json()['token']
        else:
            print("Error fetching token")
            return None
    except Exception as e:
        print("Exception fetching token:", e)
        return None

# Function to fetch emails
def get_emails(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{TEMP_MAIL_API}/messages", headers=headers)
        if response.status_code == 200:
            return response.json()["hydra:member"]
        else:
            print("Error fetching emails")
            return []
    except Exception as e:
        print("Exception fetching emails:", e)
        return []

# Function to read an email by ID
def read_email(token, email_id):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{TEMP_MAIL_API}/messages/{email_id}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error reading email")
            return None
    except Exception as e:
        print("Exception reading email:", e)
        return None

# GUI setup
class TempMailApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Interactive Temporary Mailbox")
        self.geometry("800x600")

        # Initialize variables
        self.account_id = None
        self.temp_email = None
        self.token = None
        self.email_password = None
        self.email_ids = set()

        # Create GUI elements
        self.create_widgets()

        # Generate a new temporary email
        self.generate_new_email()

    def create_widgets(self):
        # Email Frame
        self.email_frame = ctk.CTkFrame(self)
        self.email_frame.pack(pady=10, fill="x")

        # Email Label
        self.email_label = ctk.CTkLabel(self.email_frame, text="Temporary Email: Generating...", font=("Arial", 16))
        self.email_label.pack(side="left", padx=10)

        # Copy Button
        self.copy_button = ctk.CTkButton(self.email_frame, text="Copy Email", command=self.copy_email)
        self.copy_button.pack(side="right", padx=10)

        # Refresh Button
        self.refresh_button = ctk.CTkButton(self, text="Refresh Inbox", command=self.refresh_inbox)
        self.refresh_button.pack(pady=10)

        # Inbox Frame
        self.inbox_frame = ctk.CTkFrame(self)
        self.inbox_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.inbox_list = ctk.CTkScrollableFrame(self.inbox_frame, width=780, height=400)
        self.inbox_list.pack(fill="both", expand=True)

        self.inbox_headers = ctk.CTkFrame(self.inbox_list)
        self.inbox_headers.pack(fill="x")

        self.headers = ["From", "Subject", "Date"]
        for header in self.headers:
            ctk.CTkLabel(self.inbox_headers, text=header, font=("Arial", 12)).pack(side="left", padx=5, pady=5, fill="x", expand=True)

        self.inbox_rows = []

    def copy_email(self):
        if self.temp_email:
            pyperclip.copy(self.temp_email)
            messagebox.showinfo("Copied", "Temporary email copied to clipboard!")

    def add_email_row(self, email):
        row = ctk.CTkFrame(self.inbox_list)
        row.pack(fill="x", pady=2)

        from_label = ctk.CTkLabel(row, text=email["from"], font=("Arial", 12))
        from_label.pack(side="left", padx=5)

        subject_label = ctk.CTkLabel(row, text=email["subject"], font=("Arial", 12))
        subject_label.pack(side="left", padx=5)

        date_label = ctk.CTkLabel(row, text=email["createdAt"], font=("Arial", 12))
        date_label.pack(side="right", padx=5)

        row.bind("<Double-1>", lambda event, email=email: self.show_email(email["id"]))
        self.inbox_rows.append(row)

    def generate_new_email(self):
        self.account_id, self.temp_email, self.email_password = generate_temp_email()
        if self.temp_email:
            self.email_label.configure(text=f"Temporary Email: {self.temp_email}")
            self.token = get_token(self.temp_email, self.email_password)
            self.refresh_inbox()
        else:
            messagebox.showerror("Error", "Failed to generate temporary email.")

    def refresh_inbox(self):
        if self.token:
            emails = get_emails(self.token)
            for email in emails:
                if email['id'] not in self.email_ids:
                    self.email_ids.add(email['id'])
                    self.add_email_row(email)

    def show_email(self, email_id):
        email_content = read_email(self.token, email_id)
        if email_content:
            messagebox.showinfo(
                "Email Content", 
                f"From: {email_content['from']}\nSubject: {email_content['subject']}\n\n{email_content['text']}\n\nClick any verification link directly in your browser!"
            )

# Start the application
if __name__ == "__main__":
    app = TempMailApp()
    app.mainloop()
