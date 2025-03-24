import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from groq import Groq
import re
from textblob import TextBlob  # Para análise de sentimento
from translate import Translator  # Para tradução
from docx import Document  # Para exportar em .docx
import logging  # Para log de erros
import soundfile as sf  # Para manipulação de áudio
import simpleaudio as sa  # Para reprodução de áudio
import threading  # Para executar a reprodução em segundo plano

# Configuração da API da Groq
api_key = "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"  # Sua chave da Groq
client = Groq(api_key=api_key)

# Configuração do log de erros
logging.basicConfig(filename="transcricao_errors.log", level=logging.ERROR, format="%(asctime)s - %(message)s")

# Variáveis globais para controle de reprodução de áudio
audio_data = None
sample_rate = None
playing = False
play_obj = None

# Função para formatar o texto com pontuações
def formatar_texto(texto):
    texto = re.sub(r'(\w+)\s*$', r'\1.', texto)  # Ponto no final
    texto = re.sub(r'(\w+)\s+([e|ou|mas|porém]\s+)', r'\1, \2', texto)  # Vírgulas antes de conjunções
    return texto

# Função para transcrever o áudio
def transcrever_audio():
    filename = filedialog.askopenfilename(
        title="Selecione um arquivo de áudio",
        filetypes=(("Arquivos de áudio", "*.mp3 *.wav *.ogg *.flac"), ("Todos os arquivos", "*.*"))
    )

    if not filename:
        messagebox.showwarning("Aviso", "Nenhum arquivo selecionado!")
        return

    progress_bar.start(10)  # Inicia a barra de progresso

    try:
        with open(filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo",
                prompt="Inclua pontuações como vírgulas e pontos.",
                response_format="json",
                language="pt",
                temperature=0.0
            )

        texto_formatado = formatar_texto(transcription.text)
        texto_transcrito.delete(1.0, tk.END)
        texto_transcrito.insert(tk.END, texto_formatado)
        messagebox.showinfo("Sucesso", "Transcrição concluída com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro durante a transcrição: {e}")
        logging.error(f"Erro na transcrição: {e}")
    finally:
        progress_bar.stop()  # Para a barra de progresso

# Função para salvar o texto transcrito
def salvar_texto():
    texto = texto_transcrito.get(1.0, tk.END)
    if not texto.strip():
        messagebox.showwarning("Aviso", "Nenhum texto para salvar!")
        return

    filename = filedialog.asksaveasfilename(
        title="Salvar texto transcrito",
        filetypes=(("Arquivos de texto", "*.txt"), ("Documentos Word", "*.docx"), ("Todos os arquivos", "*.*")),
        defaultextension=".txt"
    )

    if filename:
        try:
            if filename.endswith(".docx"):
                doc = Document()
                doc.add_paragraph(texto)
                doc.save(filename)
            else:
                with open(filename, "w") as file:
                    file.write(texto)
            messagebox.showinfo("Sucesso", "Texto salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o arquivo: {e}")
            logging.error(f"Erro ao salvar arquivo: {e}")

# Função para traduzir o texto
def traduzir_texto():
    texto = texto_transcrito.get(1.0, tk.END)
    if not texto.strip():
        messagebox.showwarning("Aviso", "Nenhum texto para traduzir!")
        return

    try:
        translator = Translator(to_lang="en")  # Traduz para inglês
        traducao = translator.translate(texto)
        texto_transcrito.delete(1.0, tk.END)
        texto_transcrito.insert(tk.END, traducao)
        messagebox.showinfo("Sucesso", "Texto traduzido com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro durante a tradução: {e}")
        logging.error(f"Erro na tradução: {e}")

# Função para analisar o sentimento do texto
def analisar_sentimento():
    texto = texto_transcrito.get(1.0, tk.END)
    if not texto.strip():
        messagebox.showwarning("Aviso", "Nenhum texto para analisar!")
        return

    try:
        blob = TextBlob(texto)
        sentimento = blob.sentiment
        messagebox.showinfo("Análise de Sentimento", f"Polaridade: {sentimento.polarity}\nSubjetividade: {sentimento.subjectivity}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro durante a análise de sentimento: {e}")
        logging.error(f"Erro na análise de sentimento: {e}")

# Função para alternar entre temas claro e escuro
def alternar_tema():
    if root.tk_getPalette() == "#f0f0f0":
        root.tk_setPalette(background="#2d2d2d", foreground="#ffffff")
        texto_transcrito.config(bg="#1e1e1e", fg="#ffffff")
    else:
        root.tk_setPalette(background="#f0f0f0", foreground="#000000")
        texto_transcrito.config(bg="white", fg="#333333")

# Função para carregar e reproduzir o áudio
def carregar_audio():
    global audio_data, sample_rate, playing, play_obj
    filename = filedialog.askopenfilename(
        title="Selecione um arquivo de áudio",
        filetypes=(("Arquivos de áudio", "*.wav *.mp3 *.ogg *.flac"), ("Todos os arquivos", "*.*"))
    )

    if filename:
        try:
            audio_data, sample_rate = sf.read(filename)
            playing = True
            threading.Thread(target=reproduzir_audio).start()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar o áudio: {e}")

# Função para reproduzir o áudio
def reproduzir_audio():
    global playing, play_obj
    if audio_data is not None:
        play_obj = sa.play_buffer((audio_data * 32767).astype("int16"), 1, 2, sample_rate)
        playing = True
        atualizar_barra_progresso()

# Função para parar a reprodução do áudio
def parar_audio():
    global playing, play_obj
    if play_obj is not None:
        play_obj.stop()
        playing = False

# Função para atualizar a barra de progresso do áudio
def atualizar_barra_progresso():
    global playing, play_obj
    if playing and play_obj is not None:
        progresso = (play_obj.current_frame / len(audio_data)) * 100
        progresso_audio["value"] = progresso
        if play_obj.is_playing():
            root.after(100, atualizar_barra_progresso)  # Atualiza a cada 100ms
        else:
            playing = False

# Configuração da interface gráfica
root = tk.Tk()
root.title("Transcrição de Áudio com Groq")
root.configure(bg="#f0f0f0")  # Tema claro padrão

# Frame principal
main_frame = tk.Frame(root, bg="#f0f0f0")
main_frame.pack(padx=20, pady=20)

# Título
titulo = tk.Label(main_frame, text="Transcrição de Áudio com Groq", font=("Arial", 16, "bold"), bg="#f0f0f0", fg="#333333")
titulo.pack(pady=10)

# Botão para selecionar o arquivo de áudio
btn_selecionar = tk.Button(main_frame, text="Selecionar Arquivo de Áudio", command=transcrever_audio, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
btn_selecionar.pack(pady=10)

# Barra de progresso
progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=300, mode="indeterminate")
progress_bar.pack(pady=10)

# Caixa de texto com barra de rolagem para exibir o texto transcrito
texto_transcrito = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15, width=60, font=("Arial", 12), bg="white", fg="#333333")
texto_transcrito.pack(pady=10)

# Frame para botões adicionais
botoes_frame = tk.Frame(main_frame, bg="#f0f0f0")
botoes_frame.pack(pady=10)

# Botão para salvar o texto transcrito
btn_salvar = tk.Button(botoes_frame, text="Salvar Texto", command=salvar_texto, bg="#008CBA", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
btn_salvar.pack(side=tk.LEFT, padx=5)

# Botão para traduzir o texto
btn_traduzir = tk.Button(botoes_frame, text="Traduzir", command=traduzir_texto, bg="#FFA500", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
btn_traduzir.pack(side=tk.LEFT, padx=5)

# Botão para analisar sentimento
btn_sentimento = tk.Button(botoes_frame, text="Analisar Sentimento", command=analisar_sentimento, bg="#9C27B0", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
btn_sentimento.pack(side=tk.LEFT, padx=5)

# Botão para alternar tema
btn_tema = tk.Button(botoes_frame, text="Alternar Tema", command=alternar_tema, bg="#607D8B", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
btn_tema.pack(side=tk.LEFT, padx=5)

# Botão para carregar e reproduzir áudio
btn_reproduzir = tk.Button(main_frame, text="Reproduzir Áudio", command=carregar_audio, bg="#FF5722", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
btn_reproduzir.pack(pady=10)

# Botão para parar a reprodução de áudio
btn_parar = tk.Button(main_frame, text="Parar Áudio", command=parar_audio, bg="#f44336", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
btn_parar.pack(pady=10)

# Barra de progresso do áudio
progresso_audio = ttk.Progressbar(main_frame, orient="horizontal", length=300, mode="determinate")
progresso_audio.pack(pady=10)

# Botão para sair
btn_sair = tk.Button(main_frame, text="Sair", command=root.quit, bg="#f44336", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
btn_sair.pack(pady=10)

# Iniciar a interface
root.mainloop()