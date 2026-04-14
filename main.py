import streamlit as st
from PIL import Image
import io
from groq import Groq

# ─────────────────────────────────────────
# 店舗データ
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
# ページ設定
# ─────────────────────────────────────────
st.set_page_config(
    page_title="髪質改善 ビフォーアフター投稿ジェネレーター",
    page_icon="✂️",
    layout="centered",
)

st.title("✂️ 髪質改善 投稿ジェネレーター")
st.caption("ビフォーアフター画像の結合 ＋ SNS投稿文を自動生成します")

# ─────────────────────────────────────────
# APIキー（シークレット or サイドバー入力）
# ─────────────────────────────────────────
api_key = st.secrets.get("GROQ_API_KEY", "")

with st.sidebar:
    st.header("⚙️ 設定")
    if not api_key:
        api_key = st.text_input(
            "Groq APIキー",
            type="password",
            placeholder="gsk_...",
            help="console.groq.com で無料取得できます。",
        )
    else:
        st.success("✅ APIキー設定済み")
    st.markdown("---")
    st.caption("このアプリはスマートフォンからの操作を前提としています。")

# ─────────────────────────────────────────
# 入力フォーム
# ─────────────────────────────────────────
st.subheader("1. 店舗選択")
store_name = st.selectbox("店舗を選択してください", list(STORES.keys()))

st.subheader("2. ビフォーアフター画像")
col1, col2 = st.columns(2)
with col1:
    before_file = st.file_uploader("Before 画像", type=["jpg", "jpeg", "png", "webp"], key="before")
with col2:
    after_file = st.file_uploader("After 画像", type=["jpg", "jpeg", "png", "webp"], key="after")

platform = st.selectbox(
    "📐 投稿先に合わせた画像サイズ",
    [
        "Googleビジネスプロフィール（4:3 横長）",
        "Instagram フィード（4:5 縦長）",
        "Instagram 正方形（1:1）",
    ],
)
ASPECT_RATIOS = {
    "Googleビジネスプロフィール（4:3 横長）": (4, 3),
    "Instagram フィード（4:5 縦長）": (4, 5),
    "Instagram 正方形（1:1）": (1, 1),
}

st.subheader("3. 施術情報")
concern = st.text_area("ご来店時のお悩み *", placeholder="例）くせ毛でまとまらない、広がりやすい、パサつきが気になる")
region = st.text_input("お住まいの地域（任意）", placeholder="例）福岡市中央区、春日市")
booked_menu = st.text_input("ご予約時のメニュー *", placeholder="例）髪質改善トリートメント")
actual_menu = st.text_input("実際の施術メニュー（変更した場合のみ入力）", placeholder="空欄の場合は「変更なし」として扱います")
point = st.text_area("今回の施術ポイント *", placeholder="例）毛先のダメージが強かったため、酸熱トリートメントに変更し内部補修を重点的に行いました")
reaction = st.text_area("お客様の反応・頂いた声 *", placeholder="例）「こんなにサラサラになったの初めて！」と大変喜んでいただけました")
other = st.text_area("その他（任意）", placeholder="次回メニューの提案など、追記したい内容があれば")

# ─────────────────────────────────────────
# ヘルパー関数: 画像結合
# ─────────────────────────────────────────
def combine_images(before_img: Image.Image, after_img: Image.Image, aspect: tuple) -> Image.Image:
    aw, ah = aspect
    # 出力サイズを決定（長辺1080px基準）
    if aw >= ah:
        out_w, out_h = 1080, int(1080 * ah / aw)
    else:
        out_h, out_w = 1080, int(1080 * aw / ah)

    half_w = out_w // 2

    def fit_and_crop(img: Image.Image, tw: int, th: int) -> Image.Image:
        """指定サイズにセンタークロップ（各写真を均等にトリミング）"""
        scale = max(tw / img.width, th / img.height)
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - tw) // 2
        top = (new_h - th) // 2
        return img.crop((left, top, left + tw, top + th))

    before_cropped = fit_and_crop(before_img, half_w, out_h)
    after_cropped = fit_and_crop(after_img, half_w, out_h)

    collage = Image.new("RGB", (out_w, out_h), (0, 0, 0))
    collage.paste(before_cropped, (0, 0))
    collage.paste(after_cropped, (half_w, 0))
    return collage


# ─────────────────────────────────────────
# ヘルパー関数: 投稿文生成
# ─────────────────────────────────────────
def build_prompt(store_name, concern, region, booked_menu, actual_menu, point, reaction, other):
    actual_menu_text = actual_menu.strip() if actual_menu.strip() else "変更なし"
    region_text = f"（{region}在住）" if region.strip() else ""

    return f"""あなたは福岡の髪質改善専門サロンのスタイリストです。
以下の施術情報をもとに、SNS（Instagram / Googleビジネスプロフィール）向けの投稿文を生成してください。

【トーン】
固くなりすぎず、誠実で親しみやすい「髪質改善のプロ」の口調。お客様への感謝と施術へのこだわりが伝わるように。

【投稿文の構成】
1. キャッチコピー（お悩みの解決を象徴する一言。絵文字を1〜2個使ってよい）
2. お悩みと背景（地域情報があれば自然に触れる）
3. 施術のこだわり（予約メニューから変更があればプロ視点でその理由も説明）
4. お客様の喜びの声

【施術情報】
- 店舗名: {store_name}
- お客様のお悩み: {concern}{region_text}
- ご予約時のメニュー: {booked_menu}
- 実際の施術メニュー: {actual_menu_text}
- 施術ポイント: {point}
- お客様の反応・声: {reaction}
{"- その他: " + other if other.strip() else ""}

【注意事項】
- ハッシュタグや店舗情報は含めないこと（別途付与します）
- 改行を適切に入れて読みやすくすること
- 投稿文のみを出力すること（前置きや説明は不要）
"""


def generate_post(api_key, prompt):
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def build_footer(store_name):
    s = STORES[store_name]
    return f"""
━━━━━━━━━━━━━━━━━━━━
📍 {store_name}
{s['address']}
📞 {s['tel']}
🔗 {s['url']}
━━━━━━━━━━━━━━━━━━━━"""


# ─────────────────────────────────────────
# 生成ボタン
# ─────────────────────────────────────────
st.markdown("---")
generate_btn = st.button("🪄 コラージュ画像 ＆ 投稿文を生成する", use_container_width=True, type="primary")

if generate_btn:
    errors = []
    if not api_key:
        errors.append("サイドバーにGemini APIキーを入力してください。")
    if not before_file:
        errors.append("Before画像をアップロードしてください。")
    if not after_file:
        errors.append("After画像をアップロードしてください。")
    if not concern.strip():
        errors.append("「ご来店時のお悩み」を入力してください。")
    if not booked_menu.strip():
        errors.append("「ご予約時のメニュー」を入力してください。")
    if not point.strip():
        errors.append("「今回の施術ポイント」を入力してください。")
    if not reaction.strip():
        errors.append("「お客様の反応・頂いた声」を入力してください。")

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    with st.spinner("画像を結合しています..."):
        try:
            from PIL import ImageOps
            before_img = ImageOps.exif_transpose(Image.open(before_file)).convert("RGB")
            after_img = ImageOps.exif_transpose(Image.open(after_file)).convert("RGB")
            collage = combine_images(before_img, after_img, ASPECT_RATIOS[platform])

            buf = io.BytesIO()
            collage.save(buf, format="JPEG", quality=90)
            buf.seek(0)
            collage_bytes = buf.getvalue()
        except Exception as ex:
            st.error(f"画像処理中にエラーが発生しました: {ex}")
            st.stop()

    st.success("✅ コラージュ画像が完成しました！")
    st.image(collage, caption="Before ← → After", use_container_width=True)
    st.download_button(
        label="📥 コラージュ画像をダウンロード",
        data=collage_bytes,
        file_name="before_after_collage.jpg",
        mime="image/jpeg",
        use_container_width=True,
    )

    with st.spinner("Gemini AIで投稿文を生成しています..."):
        try:
            prompt = build_prompt(
                store_name, concern, region, booked_menu, actual_menu, point, reaction, other
            )
            post_body = generate_post(api_key, prompt)
        except Exception as ex:
            st.error(f"文章生成中にエラーが発生しました。APIキーを確認してください。\n{ex}")
            st.stop()

    footer = build_footer(store_name)
    full_post = f"{post_body}\n\n{HASHTAGS}\n{footer}"

    st.success("✅ 投稿文が生成されました！")
    st.subheader("📝 生成された投稿文")
    st.text_area("投稿文（コピーして使用してください）", value=full_post, height=480)
