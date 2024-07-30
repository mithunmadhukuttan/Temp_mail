import requests
import json
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

# Function to generate a random email address
def generate_temp_email():
    response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
    if response.status_code == 200:
        email = response.json()[0]
        return email
    else:
        print("Error generating email address")
        return None

# Function to get emails for a given email address
def get_emails(email):
    username, domain = email.split('@')
    url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error retrieving emails")
        return None

# Function to read an email by ID
def read_email(email, email_id):
    username, domain = email.split('@')
    url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={email_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error reading email")
        return None

# Function to refresh the inbox
def refresh_inbox():
    emails = get_emails(temp_email)
    if emails:
        for email in emails:
            if email['id'] not in email_ids:
                email_ids.add(email['id'])
                inbox_list.insert('', 'end', values=(email['from'], email['subject'], email['date'], email['id']))

# Function to periodically refresh the inbox
def periodic_refresh():
    while True:
        refresh_inbox()
        time.sleep(30)

# Function to display email content
def show_email(event):
    selected_item = inbox_list.selection()
    if selected_item:
        item = inbox_list.item(selected_item)
        email_id = item['values'][3]
        email_content = read_email(temp_email, email_id)
        if email_content:
            messagebox.showinfo("Email Content", f"From: {email_content['from']}\nSubject: {email_content['subject']}\n\n{email_content['textBody']}")

# Generate a temporary email
temp_email = generate_temp_email()
if temp_email:
    print(f"Temporary Email: {temp_email}")

    # GUI setup
    root = tk.Tk()
    root.title("Temporary Email Inbox")

    tk.Label(root, text=f"Temporary Email: {temp_email}").pack(pady=10)

    inbox_frame = ttk.Frame(root)
    inbox_frame.pack(fill='both', expand=True)

    columns = ('from', 'subject', 'date', 'id')
    inbox_list = ttk.Treeview(inbox_frame, columns=columns, show='headings')
    inbox_list.heading('from', text='From')
    inbox_list.heading('subject', text='Subject')
    inbox_list.heading('date', text='Date')
    inbox_list.heading('id', text='ID')
    inbox_list.pack(fill='both', expand=True)

    email_ids = set()

    # Bind double-click event to display email content
    inbox_list.bind('<Double-1>', show_email)

    # Start the periodic refresh in a separate thread
    threading.Thread(target=periodic_refresh, daemon=True).start()

    root.mainloop()
else:
    print("Failed to create temporary email.")
