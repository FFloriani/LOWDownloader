# 🌌 LOWDownloader

<p align="center">
  <img src="lowdownloader_logo.png" alt="LOWDownloader Logo" width="128" height="128" style="border-radius: 20%; box-shadow: 0 10px 30px rgba(160,32,240,0.3);"><br>
  <strong>Uma interface desktop moderna, minimalista e cósmica de alta performance para download, recorte e processamento de vídeos da Web.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/pywebview-v4.0%2B-darkgreen?style=for-the-badge&logo=javascript&logoColor=white" alt="pywebview">
  <img src="https://img.shields.io/badge/yt--dlp-Latest-purple?style=for-the-badge" alt="yt-dlp">
  <img src="https://img.shields.io/badge/FFmpeg-Ready-orange?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg">
</p>

---

## 🌟 O que é o LOWDownloader?

O **LOWDownloader** é uma ferramenta para criadores de conteúdo, editores de vídeo e entusiastas. Ele combina a robustez e velocidade da ferramenta de linha de comando `yt-dlp` com uma **interface de ponta acelerada por hardware (HTML5/CSS3/Tailwind)**.

Projetado especificamente para otimizar fluxos de trabalho de edição, o aplicativo elimina a necessidade de baixar vídeos inteiros de várias horas apenas para extrair alguns minutos. Cole o link, veja o preview, marque o trecho exato usando sliders interativos com **preview de frames em tempo real** e baixe apenas o necessário.

---

## ✨ Recursos de Destaque

*   **🌌 Design Cósmico Premium**: Visual imersivo inspirado nos layouts modernos AAA (como o ecossistema HoYoverse), com gradientes sutis, efeito *glassmorphism*, brilho luminescente e animações fluidas.
*   **✂️ Corte Inteligente com Preview Dinâmico**:
    *   Defina trechos específicos via sliders ou campos de tempo (`HH:MM:SS`).
    *   Conectado diretamente ao FFmpeg, extrai e exibe miniaturas dos frames dos tempos selecionados **sem precisar baixar o vídeo inteiro antes**.
    *   O `yt-dlp` faz o download cirúrgico apenas da faixa de tempo escolhida, economizando gigabytes de dados e horas de espera.
*   **🍪 Gestão Inteligente de Cookies**:
    *   Importe cookies diretamente do seu navegador preferido (Chrome, Edge, Firefox, Brave, Opera, Vivaldi, etc.) com um clique.
    *   Acesse com segurança vídeos privados, VODs de inscritos (*sub-only*) na Twitch, conteúdos exclusivos para membros no YouTube ou redes sociais privadas.
*   **📱 Conversão & Otimização Automática para WhatsApp**:
    *   Gera opcionalmente uma cópia otimizada (`*_whatsapp.mp4`) com transcodificação inteligente em H.264 Main Profile + AAC + yuv420p + 720p com Faststart (para streaming rápido).
    *   Esqueça os erros de *"arquivo não compatível"* do WhatsApp causados por CODECs modernos como AV1, VP9 ou profiles avançados a 1080p60fps.
*   **🎵 Extração de Áudio Isolado (MP3)**: Baixe apenas o áudio de lives, podcasts ou músicas com compressão direta.
*   **📋 Monitoramento Avançado & Logs**: Terminal integrado na própria interface mostrando a velocidade real de download, tamanho final e o log completo de processamento em tempo real.
*   **🖱️ Área de Transferência Inteligente**: Detecta e pré-preenche automaticamente o link de vídeo quando você copia uma URL válida para a área de transferência.

---

## 🌐 Sites Suportados

Graças ao poder do `yt-dlp`, o aplicativo oferece suporte a **centenas de plataformas**. Entre as principais:

*   **Twitch** (VODs públicas, transmissões anteriores, Clips, sub-only via cookies).
*   **YouTube** (Vídeos, Shorts, Lives concluídas, lives em andamento, membros).
*   **Facebook** (Watch, Reels, vídeos de páginas, grupos fechados e privados via cookies).
*   **Instagram & TikTok** (Reels, publicações com vídeo, downloads em alta definição).
*   **Twitter / X** (Broadcasts, Spaces gravados, posts com mídia).
*   *Kick, Vimeo, Streamable, Dailymotion, Soundcloud e mais.*

---

## 🛠️ Instalação Rápida (Apenas 1 vez)

O aplicativo foi projetado para rodar diretamente sem necessidade de instalações complexas. Siga os passos:

1.  Certifique-se de ter o **[Python 3.8+](https://www.python.org/downloads/)** instalado e marcado a opção **"Add Python to PATH"** durante a instalação.
2.  Dê um duplo clique no arquivo **`setup.bat`**.

O script irá automaticamente:
*   Verificar se o interpretador Python está disponível.
*   Instalar/atualizar o `yt-dlp` para a versão mais recente.
*   Instalar as bibliotecas necessárias: `pywebview`, `pillow` (processamento de imagens) e `imageio-ffmpeg` (que baixa automaticamente um executável leve e estável do `ffmpeg.exe` de ~30MB).

> 💡 **FFmpeg Personalizado:** Se você já possui o FFmpeg instalado no seu sistema ou deseja usar a sua própria build, basta copiar o `ffmpeg.exe` para a pasta `bin/` na raiz do projeto. O LOWDownloader priorizará este executável automaticamente.

---

## 🚀 Como Usar

1.  Execute o aplicativo dando um duplo clique em **`LOWDownloader.bat`**.
2.  **Insira a URL**: Cole o link do vídeo desejado e clique em **Verificar**. O app buscará instantaneamente o título, autor, duração e a miniatura principal.
3.  **Configure o Download**:
    *   Escolha a **Qualidade** desejada (a opção *Source* baixa a qualidade original sem perda).
    *   *(Opcional)* Ative **Cortar trecho** para definir os tempos de início e fim.
    *   *(Opcional)* Ative **Somente áudio (MP3)** se deseja apenas a trilha sonora.
    *   *(Opcional)* Ative **Otimizar p/ WhatsApp** para gerar o arquivo ultra-compatível.
    *   *(Opcional)* Caso o vídeo seja privado ou restrito, selecione seu navegador na lista de **Cookies**. *(Lembre-se de fechar as abas do navegador referentes ao site ou o próprio navegador para liberar o acesso ao banco de dados de cookies).*
4.  Escolha a pasta de destino (o padrão é a pasta `downloads/` na raiz do projeto).
5.  Clique em **BAIXAR** e acompanhe a barra de progresso e o log técnico em tempo real!

---

## 📁 Estrutura de Pastas

```text
LOWDownloader/
├── .cache/                    # Cache local temporário para thumbnails e previews
├── bin/                       # Executáveis locais opcionais (ffmpeg.exe, ffprobe.exe)
├── downloads/                 # Pasta padrão gerada para salvar os arquivos baixados
├── LOWDownloader.bat          # Launcher principal (inicia sem console preto chato)
├── lowdownloader.pyw          # Código-fonte Python integrado à interface webview
├── lowdownloader_logo.png     # Logo oficial em alta resolução
├── lowdownloader_logo.ico     # Ícone nativo multi-resolução do Windows
├── requirements.txt           # Lista de dependências Python
├── README.md                  # Documentação detalhada
└── setup.bat                  # Script de instalação automatizada das dependências
```

---

## 🔧 Atualizações Importantes

Plataformas como YouTube e Twitch alteram frequentemente suas APIs e players. Se em algum momento o download de vídeos falhar ou comportar-se de maneira inesperada, basta **executar novamente o `setup.bat`**. Ele atualizará o motor interno do `yt-dlp` para a versão mais estável disponível.

---

## 📜 Licença e Tecnologias

Este projeto foi construído sobre uma pilha tecnológica de alta confiabilidade:
*   [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Licença UNLICENSE.
*   [PyWebView](https://github.com/r0x8f/pywebview) - Visualização web robusta integrada ao Windows WebView2.
*   [FFmpeg](https://ffmpeg.org/) - Processador multimídia universal.
*   Tailwind CSS / Inter Font - Experiência visual rica e adaptada.

---
*Desenvolvido com foco em estética premium, velocidade e praticidade máxima.*
