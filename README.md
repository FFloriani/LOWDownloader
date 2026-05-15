# Decreepy Downloader

Ferramenta com interface grafica para baixar VODs / Clips da Twitch, videos do Facebook, YouTube e qualquer outro site suportado pelo `yt-dlp`. Pensada pra fluxo de edicao: cole a URL, escolha qualidade, opcionalmente recorte um trecho com preview de frames, baixa.

## Sites suportados

Qualquer um suportado pelo [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) — entre eles:

- **Twitch** — VODs publicas, Clips, sub-only (com cookies)
- **YouTube** — videos, Shorts, lives gravadas, clips, conteudo de membros (com cookies)
- **Facebook** — `facebook.com/watch`, `facebook.com/USER/videos`, Reels, `fb.watch`, videos privados (com cookies)
- **Twitter / X** — tweets com video, broadcasts, Spaces (gravados)
- **Instagram, TikTok, Kick, Vimeo, Streamable, Dailymotion**, e centenas de outros

## Instalacao (1x)

Da um duplo clique em `setup.bat`. Ele:

1. Confere se o Python esta instalado.
2. Instala/atualiza o `yt-dlp` via pip.
3. Instala o `imageio-ffmpeg` via pip — pacote que ja vem com `ffmpeg.exe` embutido (~30MB).

Se voce preferir um `ffmpeg` proprio, e so colocar `ffmpeg.exe` em `bin\` ou no PATH do sistema — o app prioriza esses caminhos antes do imageio.

## Uso

Duplo clique em `Decreepy Downloader.bat`.

1. **Cole a URL** — Twitch (`twitch.tv/videos/...`), Facebook (`facebook.com/watch?v=...`, `facebook.com/USER/videos/...`, `fb.watch/...`), YouTube ou outro.
2. Clique **Verificar** — aparece a thumbnail do video, titulo, canal e duracao.
3. Escolha a **qualidade** (Source = original).
4. (Opcional) Marque **Cortar trecho**: aparecem dois sliders (inicio / fim) ao lado dos campos `HH:MM:SS`. Conforme voce arrasta o slider ou edita o tempo, a **miniatura do frame naquele momento** aparece embaixo (extracao via ffmpeg, sem baixar a VOD inteira). O `yt-dlp` baixa so o pedaco — nao precisa pegar 8h pra usar 20 min.
5. (Opcional) Marque **Somente audio (MP3)** se quiser so o audio.
6. (Opcional) Marque **Otimizar p/ WhatsApp** — depois do download, o app gera uma copia `*_whatsapp.mp4` reencodada em H.264 Main + AAC + yuv420p + 720p + 30fps + faststart. Resolve "arquivo nao compativel" do WhatsApp (causa comum: video do Facebook em **AV1**, ou Twitch em 60fps / 1080p / profile High).
7. (Opcional) Para videos privados / sub-only / restritos, escolha em **Cookies do navegador** o navegador onde voce esta logado (Chrome, Firefox, Edge, etc.). O `yt-dlp` usa esses cookies pra acessar o conteudo. *Feche o navegador antes* ou pelo menos a aba do site (alguns navegadores travam o cookie store enquanto a janela esta aberta).
8. Escolha a pasta destino (padrao: `downloads/`).
9. **BAIXAR**.

> **Demorando pra mostrar progresso?** VODs longas em HLS (Twitch / FB) sao baixadas em centenas de fragmentos pequenos. O percentual demora alguns segundos pra aparecer enquanto o `yt-dlp` lista os fragmentos. O status acima do log atualiza com qualquer atividade — se ele estiver mudando, esta tudo certo.

## Atalhos uteis

- O nome do arquivo sai como `Canal - Titulo [id_da_vod].mp4`, com caracteres restritos (sem `/\:` etc) — pronto pra mover/editar.
- `Abrir pasta` abre a pasta de downloads.
- `Cancelar` interrompe um download em andamento.

## Pra atualizar o yt-dlp depois

A Twitch muda coisa no backend de tempos em tempos. Se algum dia parar de funcionar, rode `setup.bat` de novo — ele faz `pip install --upgrade yt-dlp`.

## Estrutura

```
Decreepy Downloader/
├── decreepy.pyw              # GUI principal
├── Decreepy Downloader.bat   # launcher
├── setup.bat                 # instala dependencias
├── bin/
│   ├── ffmpeg.exe
│   └── ffprobe.exe
└── downloads/                # criado no 1o uso
```

## Por que yt-dlp?

E o fork mantido do youtube-dl. Suporta centenas de sites nativamente. Para conteudo privado / com login, o app permite escolher de qual navegador puxar cookies — ja resolvido pela UI.
