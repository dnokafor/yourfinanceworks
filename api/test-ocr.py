from ollama_ocr import OCRProcessor

# Initialize OCR processor
ocr = OCRProcessor(model_name='llama3.2-vision:11b', base_url="http://localhost:11434/api/generate")  # You can use any vision model available on Ollama
# you can pass your custom ollama api

if __name__ == "__main__":
    # Process an image
    result = ocr.process_image(
        image_path="receipt.jpg",  # path to your pdf files "path/to/your/file.pdf"
        format_type="json",  # Options: markdown, text, json, structured, key_value
        # custom_prompt=(
        #     "Extract expense fields as JSON with keys: amount, currency, expense_date (YYYY-MM-DD), "
        #     "category, vendor, tax_rate, tax_amount, total_amount, payment_method, reference_number, notes."
        # ),
        custom_prompt=(
            "You are an OCR parser. Extract key expense fields and respond ONLY with compact JSON. "
            "Required keys: amount, currency, expense_date (YYYY-MM-DD), category, vendor, tax_rate, tax_amount, total_amount, payment_method, reference_number, notes. "
            "If a field is unknown, set it to null. Do not include any prose."
        ),
        language="English"
    )
    print(result)
