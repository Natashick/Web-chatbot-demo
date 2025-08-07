# score_backup_fixed.py
import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
from transformers.modeling_utils import PreTrainedModel
from peft import PeftModel, PeftConfig

# Optional: Authenticate to Hugging Face Hub if token is provided
try:
    from huggingface_hub import login
    hf_token = os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if hf_token:
        login(token=hf_token)
except ImportError:
    pass  # huggingface_hub not installed, skip

model = None
tokenizer = None
generator = None

def init():
    global model, tokenizer, generator
    model_dir = os.environ["AZUREML_MODEL_DIR"]
    fixed_subdir = "mistral-finetune-job-20250625100239"
    config_dir = os.path.join(model_dir, fixed_subdir)
    if not os.path.exists(config_dir):
        subdirs = [d for d in os.listdir(model_dir) if os.path.isdir(os.path.join(model_dir, d))]
        if not subdirs:
            raise RuntimeError("No subdirectory found in model directory!")
        config_dir = os.path.join(model_dir, subdirs[0])
        print(f"[DEBUG] Fallback: using first subdir {config_dir}")
    else:
        print(f"[DEBUG] Using fixed subdir {config_dir}")
    print(f"[DEBUG] models dir contents: {os.listdir(config_dir)}")

    peft_config = PeftConfig.from_pretrained(config_dir, local_files_only=True)
    BASE_MODEL_ID = peft_config.base_model_name_or_path
    print(f"[DEBUG] BASE_MODEL_ID from adapter config: {BASE_MODEL_ID}")
    if BASE_MODEL_ID != "mistralai/Mistral-7B-v0.1":
        print(f"[WARNING] Adapter expects base model mistralai/Mistral-7B-v0.1, but got: {BASE_MODEL_ID}")

    tokenizer = AutoTokenizer.from_pretrained(config_dir, use_fast=False, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    bnb_conf = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        device_map="auto",
        trust_remote_code=True,
        quantization_config=bnb_conf,
    )
    model = PeftModel.from_pretrained(base_model, config_dir)
    model.eval()

    generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )
    if generator is None:
        raise RuntimeError("Failed to create text-generation pipeline. Check model and tokenizer setup.")

def run(raw_data):
    global generator, tokenizer
    if generator is None:
        init()
    if generator is None:
        raise RuntimeError("[ERROR] generator is still None after init(). Check model and pipeline setup in init().")
    if isinstance(raw_data, str):
        data = json.loads(raw_data)
    else:
        data = raw_data

    prompts = data.get("prompt")
    extra_fields = {k: v for k, v in data.items() if k != "prompt"}

    if prompts is None:
        return [{"error": "No prompt provided."}]

    if isinstance(prompts, str):
        prompts = [prompts]
    elif not isinstance(prompts, list):
        return [{"error": "Prompt must be a string or a list of strings."}]

    results = []
    for idx, prompt in enumerate(prompts):
        # Korrektes Format für finegetuned Mistral-7B (wie im ursprünglichen Training)
        formatted = f"<s>Question: {prompt.strip()}\nAnswer:"
        
        # Dynamische Token-Anpassung basierend auf Fragetyp
        prompt_lower = prompt.lower().strip()
        
        # Erhöhte Token-Limits für vollständigere Antworten
        # Kurze Antworten für einfache Fragen
        if any(word in prompt_lower for word in ['what is', 'was ist', 'define', 'definiere']):
            if len(prompt.split()) <= 4:  # Sehr kurze Fragen
                max_tokens = 200  # Erhöht von 100
            else:
                max_tokens = 300  # Erhöht von 200
        
        # Längere Antworten für komplexe Fragen
        elif any(word in prompt_lower for word in ['explain', 'describe', 'how', 'why', 'compare', 'analyze', 'erkläre', 'beschreibe', 'wie', 'warum', 'vergleiche']):
            max_tokens = 500  # Erhöht von 400
        
        # Sehr lange Antworten für sehr komplexe Fragen
        elif any(word in prompt_lower for word in ['methods', 'methodn', 'different', 'verschiedene', 'all', 'alle', 'process', 'prozess', 'step by step', 'schritt für schritt']):
            max_tokens = 700  # Erhöht von 600
        
        # Standard für alles andere
        else:
            max_tokens = 350  # Erhöht von 250
        
        try:
            gen = generator(
                formatted,
                max_new_tokens=max_tokens,
                num_return_sequences=1,
                do_sample=True,
                top_k=20,  # Reduziert von 50 - weniger kreative Wörter
                top_p=0.7,  # Reduziert von 0.9 - konservativer
                temperature=0.3,  # Stark reduziert von 0.6 - weniger Kreativität
                pad_token_id=tokenizer.pad_token_id if tokenizer else None,
                eos_token_id=tokenizer.eos_token_id if tokenizer else None,
                repetition_penalty=1.2  # Erhöht von 1.1 - noch weniger Wiederholungen
            )
            text = gen[0]["generated_text"] if isinstance(gen, list) and "generated_text" in gen[0] else str(gen)

            # Extrahiere nur den Antwort-Teil
            if "Answer:" in text:
                answer_part = text.split("Answer:", 1)[1].strip()
            else:
                answer_part = text.replace(formatted, "").strip()
            
            # Stoppe bei der nächsten Frage (falls vorhanden)
            if "Question:" in answer_part:
                answer_part = answer_part.split("Question:")[0].strip()
            
            # Entferne weitere störende Tokens
            cleaned = answer_part
            for remove_token in ["Answer:", "answer:", "Question:", "question:"]:
                cleaned = cleaned.replace(remove_token, "").strip()
            
            # Intelligente Antwort-Bereinigung
            def clean_answer_intelligently(text):
                # 1. Entferne übermäßige Wiederholungen
                words = text.split()
                filtered_words = []
                last_word = ""
                repeat_count = 0
                
                for word in words:
                    if word.lower() == last_word.lower():
                        repeat_count += 1
                        if repeat_count < 3:  # Max 2 Wiederholungen
                            filtered_words.append(word)
                    else:
                        filtered_words.append(word)
                        repeat_count = 0
                    last_word = word
                
                text = " ".join(filtered_words)
                
                # 2. Stoppe bei logischen Endpunkten
                sentences = text.split('.')
                final_sentences = []
                
                for i, sentence in enumerate(sentences):
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    # Erkenne Wiederholungsschleifen
                    if i > 0 and len(final_sentences) > 0:
                        # Prüfe ob dieser Satz zu ähnlich zum vorherigen ist
                        prev_words = set(final_sentences[-1].lower().split())
                        curr_words = set(sentence.lower().split())
                        
                        # Wenn mehr als 70% der Wörter gleich sind, stoppe
                        if len(prev_words) > 0:
                            overlap = len(prev_words.intersection(curr_words)) / len(prev_words)
                            if overlap > 0.7:
                                break
                    
                    # Erkenne unvollständige oder fehlerhafte Sätze
                    if (len(sentence.split()) > 3 and 
                        not sentence.startswith(('what is', 'was ist', 'question:', 'answer:')) and
                        not any(char in sentence for char in ['???', '...', '####'])):
                        final_sentences.append(sentence)
                    
                    # Stoppe bei zu vielen Sätzen (verhindert endlose Ausgaben)
                    if len(final_sentences) >= 8:
                        break
                
                # Rekonstruiere Text
                if final_sentences:
                    result = '. '.join(final_sentences)
                    if not result.endswith('.'):
                        result += '.'
                    return result.strip()
                else:
                    return text.strip()
            
            cleaned = clean_answer_intelligently(cleaned)

            # Überprüfe auf Halluzination oder unpassende Antworten
            def validate_answer(answer, original_prompt):
                answer_lower = answer.lower()
                
                # Warnsignale für Halluzination
                hallucination_signals = [
                    "according to", "based on research", "studies show", 
                    "it is widely known", "generally", "typically",
                    "commonly used", "often used", "usually"
                ]
                
                # Wenn die Antwort Halluzinations-Signale enthält
                if any(signal in answer_lower for signal in hallucination_signals):
                    return "I can only provide information based on the specific documentation I was trained on. I don't have enough reliable information to answer this question accurately."
                
                # Wenn die Antwort zu allgemein oder vage ist
                if len(answer.split()) < 5:
                    return "I don't have enough specific information in my training data to provide a detailed answer to this question."
                
                return answer
            
            # Validiere die Antwort
            cleaned = validate_answer(cleaned, prompt)
            
            # Falls die Antwort immer noch leer oder zu kurz ist
            if not cleaned or len(cleaned.split()) < 3:
                cleaned = "I don't have enough information in my training documentation to answer this question accurately."

            result = {
                "prompt": prompt,
                "answer": cleaned,
                "full_response": text
            }
            for k, v in extra_fields.items():
                if isinstance(v, list) and len(v) == len(prompts):
                    result[k] = v[idx]
                else:
                    result[k] = v
            results.append(result)
        except Exception as e:
            results.append({"prompt": prompt, "error": str(e)})

    return results

# Optional: Lokaler Test mit FastAPI
if __name__ == "__main__":
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI()
        
        class PromptRequest(BaseModel):
            prompt: str
        
        @app.post("/score")
        async def score_endpoint(request: PromptRequest):
            try:
                result = run({"prompt": request.prompt})
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        port = int(os.environ.get("PORT", 5001))
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except ImportError:
        print("[INFO] FastAPI/Uvicorn not available for local testing. This is expected in AzureML.")
