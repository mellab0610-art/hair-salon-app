import streamlit as st
from PIL import Image, ImageOps
import io
from groq import Groq

# ─────────────────────────────────────────
# 1. 店舗データ設定（定型情報）
# ─────────────────────────────────────────
STORES = {
    "福岡美髪研究所Knops": {
        "address": "福岡県福岡市中央区天神1-13-19 天神MARUビル4F",
        "tel": "092-711-9009",
        "url": "https://beauty.hotpepper.jp/slnH000421965/",
    },
    "髪質改善サロンBud": {
        "address": "福岡県福岡市博多区元町1-6-16 高倉ビル1F",
        "tel": "092-572-8777",
        "url": "https://beauty.hotpepper.jp/slnH000535109/",
    },
    "髪質改善broto": {
        "address": "福岡県福岡市中央区渡辺通5-24-30 東カン福岡第一キャステール 901号",
        "tel": "092-732-5230",
        "url": "https://beauty.hotpepper.jp/slnH000727386/",
    },
    "髪質改善Enit": {
        "address": "福岡県福岡市南区大橋4-13-38 1F",
        "tel": "092-235-5526",
        "url": "https://beauty.hotpepper.jp/slnH000803264/?cstt=19",
    },
}

HASHTAGS = "#福岡髪質改善 #福岡縮毛矯正 #福岡トリートメント"

# ─────────────────────────────────────────
# 2. ページ基本設定
# ─────────────────────────────────────────
st.set_page_config(
    page_title="髪質改善 投稿ジェネレーター",
    page_icon="✂️",
    layout="centered",
)

st.title("✂️ 髪質改善 投稿ジェネレーター")
st.caption("ビフォーアフター画像の結合 ＋ SNS投稿文を自動生成します")

# ─────────────────────────────────────────
# 3. APIキー設定
# ─────────────────────────────────────────
# StreamlitのSecretsまたはサイドバーから取得
api_key = st.secrets.get("GROQ_API_KEY", "")

with st.sidebar:
    st.header("⚙️ 設定")
    if not api_key:
        api_key = st.text_input("Groq APIキーを入力", type="password")
    else:
        st.success("✅ APIキー設定済み")
    st.info("スマホの方は、生成された画像を『長押し』で保存するのが確実です。")

# ─────────────────────────────────────────
# 4. 入力フォーム（UI）
# ─────────────────────────────────────────
st.subheader("1. 店舗選択")
store_name = st.selectbox("店舗を選択してください", list(STORES.keys()))

st.subheader("2. ビフォーアフター画像")
col1, col2 = st.columns(2)
with col1:
    before_file = st.file_uploader("Before 画像", type=["jpg", "jpeg", "png", "webp"])
with col2:
    after_file = st.file_uploader("After 画像", type=["jpg", "jpeg", "png", "webp"])

platform = st.selectbox(
    "📐 出力サイズ（投稿先に合わせて調整）",
    ["Googleビジネスプロフィール（4:3 横長）", "Instagram フィード（4:5 縦長）", "Instagram 正方形（1:1）"]
)

ASPECT_RATIOS = {
    "Googleビジネスプロフィール（4:3 横長）": (4, 3),
    "Instagram フィード（4:5 縦長）": (4, 5),
    "Instagram 正方形（1:1）": (1, 1),
}

st.subheader("3. 施術情報")
concern = st.text_area("ご来店時のお悩み *", placeholder="パサつきと広がりが気になる...")
region = st.text_input("お住まいの地域（任意）", placeholder="例：北九州市")
booked_menu = st.text_input("ご予約時のメニュー *", placeholder="例：カット＋カラー")
actual_menu = st.text_input("実際の施術メニュー", placeholder="変更なしの場合は空欄")
point = st.text_area("今回の施術ポイント *", placeholder="内部補修をメインに艶が出る配合に...")
reaction = st.text_area("お客様の反応・頂いた声 *", placeholder="「自分の髪じゃないみたい！」と喜んでいただけた")
other = st.text_area("その他（任意）")

# ─────────────────────────────────────────
# 5. ロジック関数
# ─────────────────────────────────────────

def combine_images(before_img, after_img, aspect):
    aw, ah = aspect
    out_w, out_h = (1080, int(1080 * ah / aw)) if aw >= ah else (int(1080 * aw / ah), 1080)
    half_w = out_w // 2

    def fit_and_pad(img, tw, th):
        img.thumbnail((tw, th), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (tw, th), (255, 255, 255))
        canvas.paste(img, ((tw - img.width) // 2, (th - img.height) // 2))
        return canvas

    b_fitted = fit_and_pad(before_img, half_w, out_h)
    a_fitted = fit_and_pad(after_img, half_w, out_h)
    collage = Image.new("RGB", (out_w, out_h))
    collage.paste(b_fitted, (0, 0))
    collage.paste(a_fitted, (half_w, 0))
    return collage

def generate_post(api_key, store_name, concern, region, booked_menu, actual_menu, point, reaction, other):
    client = Groq(api_key=api_key)
    actual = actual_menu if actual_menu.strip() else "変更なし"
    reg_text = f"（{region}よりご来店）" if region.strip() else ""
    
    prompt = f"""あなたは福岡の髪質改善専門サロンのスタイリストです。誠実で親しみやすい口調で投稿文を作ってください。
    【情報】
    店舗: {store_name} / お悩み: {concern}{reg_text} / 予約: {booked_menu} / 施術: {actual} / ポイント: {point} / 感想: {reaction} / その他: {other}
    【構成】1.キャッチコピー 2.悩みと背景 3.施術のこだわり 4.お客様の声
    ※ハッシュタグと店舗情報は不要です。"""

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

# ─────────────────────────────────────────
# 6. 実行・出力
# ─────────────────────────────────────────
st.markdown("---")
if st.button("🪄 投稿セットを生成する", use_container_width=True, type="primary"):
    if not api_key or not before_file or not after_file or not concern:
        st.error("必須項目（APIキー、画像2枚、お悩み）を確認してください。")
    else:
        with st.spinner("作成中..."):
            # 画像処理
            b_img =
