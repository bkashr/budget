import tkinter as tk

def create_window():
    window = tk.Tk()
    window.title("Budget Tracker")
    window.geometry("1000x800")
    window.configure(bg="white")
    create_widgets(window)
    window.mainloop()
   
def create_widgets(window):
    #Creating the columns for categories so they can be resized proportionally when the window is resized
    window.columnconfigure(0, weight=1)
    window.columnconfigure(1, weight=1) 
    window.columnconfigure(2, weight=1)
    window.columnconfigure(3, weight=1)
    window.columnconfigure(4, weight=1)
    #Creating the labels for the categories
    label = tk.Label(window, text="Budget Tracker", font=("Arial", 20))
    label.grid(pady=20, row=0,column = 2)
    label = tk.Label(window, text="Categories", font=("Arial", 14))
    label.grid(pady=10, row=1, column=2)
    label = tk.Label(window, text="Groceries", font=("Arial", 12))
    label.grid(pady=10, row=2, column=1)
    label = tk.Label(window, text="Entertainment", font=("Arial", 12))
    label.grid(pady=10, row=3, column=1)
    label = tk.Label(window, text="Clothing", font=("Arial", 12))
    label.grid(pady=10, row=4, column=1)
    label = tk.Label(window, text="Savings", font=("Arial", 12))
    label.grid(pady=10, row=5, column=1)
    label = tk.Label(window, text="Debt/Loans", font=("Arial", 12))
    label.grid(pady=10, row=6, column=1)
    label = tk.Label(window, text="Family/Home", font=("Arial", 12))
    label.grid(pady=10, row=2, column=3)
    label = tk.Label(window, text="Transportation", font=("Arial", 12))
    label.grid(pady=10, row=3, column=3)
    label = tk.Label(window, text="Health/Medical", font=("Arial", 12))
    label.grid(pady=10, row=4, column=3)
    label = tk.Label(window, text="Insurance", font=("Arial", 12))
    label.grid(pady=10, row=5, column=3)
    label = tk.Label(window, text="Other", font=("Arial", 12))
    label.grid(pady=10, row=6, column=3)
    

create_window()