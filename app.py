"""Gradio UI. Run: python app.py"""
import os
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
import gradio as gr
from logic import TONES, prepare_messages
from provider import complete, ModelError


def generate(draft, recipient, tone):
    try:
        messages = prepare_messages(draft, recipient, tone)
    except ValueError as error:
        return "", str(error)
    try:
        return complete(messages), "Готово. Перевірте факти й за потреби уточніть пропуски перед надсиланням."
    except ModelError as error:
        return "", str(error)


def build_demo():
    with gr.Blocks(title="ЛистОК — помічник ділового листування", analytics_enabled=False) as demo:
        gr.Markdown("# ✉️ ЛистОК\n### Від чернетки до зрозумілого листа\n"
                    "Вкажіть думки своїми словами, оберіть тон — отримайте тему й текст українською.")
        with gr.Row():
            with gr.Column():
                draft = gr.Textbox(label="Чернетка", lines=9, max_length=5000,
                    placeholder="Наприклад: Дякую за пропозицію. Попроси надіслати 3 варіанти до 30 жовтня. Бюджет 2000 грн.")
                recipient = gr.Textbox(label="Кому пишемо? (необов’язково)",
                                      placeholder="Колезі, клієнту, команді…", max_length=120)
                tone = gr.Radio(list(TONES), value=TONES[0], label="Тон листа")
                submit = gr.Button("Підготувати лист", variant="primary")
            with gr.Column():
                result = gr.Textbox(label="Готовий лист", lines=17, interactive=False)
                status = gr.Textbox(label="Стан", interactive=False)
        gr.Examples([
            ["Дякую за пропозицію. Попроси надіслати 3 варіанти до 30 жовтня. Бюджет 2000 грн.", "Партнеру", "Нейтральний"],
            ["Дякую команді за допомогу з презентацією. Матеріали отримано.", "Команді", "Дружній"],
            ["Напиши клієнту про готовність замовлення. Дата і номер замовлення невідомі.", "Клієнту", "Офіційний"],
        ], [draft, recipient, tone], label="Спробуйте приклад")
        gr.ClearButton([draft, recipient, result, status], value="Очистити")
        gr.Markdown("**Перед надсиланням перевірте факти.** Модель може помилятися. "
            "Не вводьте паролі, API-ключі й конфіденційні дані. Чернетка передається "
            "OpenRouter та обраному ним постачальнику моделі. Застосунок не надсилає листи.")
        submit.click(generate, [draft, recipient, tone], [result, status],
                     concurrency_limit=1, api_name=False)
    return demo


if __name__ == "__main__":
    build_demo().queue(max_size=8).launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")),
                                        show_error=False)
