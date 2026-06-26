# 🍔 Burger Viral — Encontrador de Vídeos Virais

App web que busca os vídeos mais virais de hamburgueria no **TikTok** e **Instagram** para você replicar no seu perfil.

---

## 🚀 Deploy no Render (online, sem precisar do computador ligado)

### Passo 1 — Subir no GitHub

1. Acesse **https://github.com/new** e crie um repositório chamado `burger-viral` (deixe como **Public** ou **Private**)
2. Na sua máquina, dentro da pasta `hamburgueria-viral`, rode os comandos:

```bash
git init
git add .
git commit -m "primeiro commit"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/burger-viral.git
git push -u origin main
```

> Substitua `SEU_USUARIO` pelo seu usuário do GitHub.

---

### Passo 2 — Obter a API Key gratuita (RapidAPI)

Você precisa de **uma única chave** do RapidAPI para buscar no TikTok e Instagram.

1. Acesse **https://rapidapi.com** e crie uma conta gratuita
2. Assine o plano **Basic (gratuito)** do TikTok Scraper → [tiktok-scraper7](https://rapidapi.com/tikwm-tikwm-default/api/tiktok-scraper7)
3. Assine o plano **Basic (gratuito)** do Instagram Scraper → [instagram-scraper-api2](https://rapidapi.com/contact-cmWXKs8V2q/api/instagram-scraper-api2)
4. Vá em **My Apps** no RapidAPI e copie sua **X-RapidAPI-Key**

---

### Passo 3 — Criar o serviço no Render

1. Acesse **https://render.com** e faça login com sua conta GitHub
2. Clique em **New → Web Service**
3. Selecione o repositório `burger-viral`
4. As configurações já são detectadas automaticamente pelo `render.yaml`. Confirme:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Em **Environment Variables**, clique em **Add Environment Variable**:
   - **Key:** `RAPIDAPI_KEY`
   - **Value:** (cole sua chave do RapidAPI)
6. Clique em **Create Web Service**

Aguarde ~2 minutos e pronto! O Render vai te dar uma URL tipo:
`https://burger-viral.onrender.com` 🎉

---

## 💻 Rodar localmente (opcional)

```bash
cp .env.example .env
# Edite o .env e cole sua RAPIDAPI_KEY

pip install -r requirements.txt
python app.py
# Acesse: http://localhost:5000
```

---

## 🎯 Como usar o app

1. Digite uma hashtag (ex: `hamburgueria`, `smashburger`, `lanche`)
2. Escolha a plataforma: TikTok, Instagram ou ambos
3. Ordene por curtidas, visualizações ou comentários
4. Clique em **"Ver vídeo original"** para se inspirar e replicar!

### Hashtags recomendadas:
`hamburgueria` · `smashburger` · `hamburguerartesanal` · `burgersofinstagram` · `foodporn` · `lanche` · `burgerbrasil`

---

## ⚠️ Limites do plano gratuito

| Plataforma | Plano gratuito |
|------------|---------------|
| TikTok     | ~100 req/mês  |
| Instagram  | ~50 req/mês   |

Suficiente para garimpagem semanal de tendências.

---

## 💡 Dicas para replicar vídeos virais

- Identifique o padrão: thumbnail chamativa, texto na tela, música em alta
- Adapte para sua realidade com o seu produto
- Poste entre 11h-13h e 18h-20h (horário de pico para comida)
- Use as mesmas hashtags do vídeo que está replicando

---

Feito com ❤️ para ajudar hamburguerias a crescer no Instagram!
