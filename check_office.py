import win32com.client
import os

try:
    # Tenta criar uma instância do Word
    word = win32com.client.Dispatch("Word.Application")
    print("Microsoft Word está instalado e acessível")
    word.Quit()
    
    # Tenta criar uma instância do Excel
    excel = win32com.client.Dispatch("Excel.Application")
    print("Microsoft Excel está instalado e acessível")
    excel.Quit()
    
    # Tenta criar uma instância do PowerPoint
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    print("Microsoft PowerPoint está instalado e acessível")
    ppt.Quit()
    
except Exception as e:
    print(f"Erro ao acessar o Office: {e}")
    print("\nSe o Office não estiver instalado, instale o Microsoft Office ou o Microsoft 365.")
    print("Se já tiver o Office instalado, tente reparar a instalação pelo Painel de Controle.")