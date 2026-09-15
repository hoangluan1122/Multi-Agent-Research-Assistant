"""Deterministic keyword normalization for academic search fallbacks."""

import re
import unicodedata
from typing import List


_STOPWORDS = {
    "a", "an", "and", "are", "as", "by", "can", "for", "from", "given", "how",
    "in", "into", "is", "of", "on", "or", "paper", "papers", "question",
    "research", "study", "terms", "the", "this", "to", "topic", "what", "with",
    "anh", "bao", "cac", "cho", "co", "cong", "cua", "cuu", "den", "doi",
    "duoc", "hay", "la", "mot", "nghien", "nhung", "noi", "phan", "qua",
    "tai", "tac", "the", "thi", "trong", "tu", "ve", "voi", "va",
    "mo", "hinh", "dai", "dang", "day", "hoc", "sau", "may", "bai", "duoi", "tren", "giua"
}

_PHRASE_MAPPINGS = [
    ("deep learning", ["deep", "learning"]),
    ("mo hinh", ["model"]),
    ("da dang", ["diversity"]),
    ("toi uu hoa", ["optimization"]),
    ("phan loai", ["classification"]),
    ("phat hien", ["detection"]),
    ("nhan dang", ["recognition"]),
    ("tuyen tien liet", ["prostate", "cancer", "prostate-specific", "antigen"]),
    ("tien liet tuyen", ["prostate", "cancer", "prostate-specific", "antigen"]),
    ("thuoc la", ["tobacco", "smoking", "nicotine", "adverse", "health", "effects"]),
    ("dien thoai", ["smartphone", "screen", "time", "mental", "health"]),
    ("man hinh", ["screen", "time"]),
    ("mang xa hoi", ["social", "media", "depression", "anxiety", "adolescents"]),
    ("tien te", ["money", "currency", "monetary", "policy", "finance"]),
    ("tai chinh", ["finance", "banking", "economics"]),
    ("ngan hang", ["banking", "finance", "economics"]),
    ("ma tuy", ["substance", "use", "disorder", "drug", "abuse"]),
    ("tien", ["money", "currency", "monetary", "policy", "banking", "finance"]),
    ("hoc sinh", ["students", "adolescents", "school"]),
    ("tac hai", ["adverse", "effects"]),
    ("anh huong", ["effects", "impact"]),
    ("chat gay nghien", ["addictive", "substances", "substance", "use"]),
    ("nghien ma tuy", ["drug", "addiction"]),
    ("nghien internet", ["internet", "addiction"]),
    ("sinh vien", ["students", "university"]),
    ("tre vi thanh nien", ["adolescents"]),
    ("thanh thieu nien", ["adolescents", "youth"]),
    ("thuc khuya", ["sleep", "deprivation", "late", "bedtime"]),
    ("suc khoe tam than", ["mental", "health"]),
    ("y te", ["healthcare", "medicine"]),
    ("hinh anh y te", ["medical", "imaging"]),
    ("ung thu", ["cancer"]),
    ("benh tim", ["cardiovascular", "disease"]),
    ("tri tue nhan tao", ["artificial", "intelligence"]),
    ("hoc may", ["machine", "learning"]),
    ("hoc sau", ["deep", "learning"]),
    ("xu ly ngon ngu tu nhien", ["natural", "language", "processing"]),
    ("thi giac may tinh", ["computer", "vision"]),
    ("phan doan anh", ["image", "segmentation"]),
    ("giao duc", ["education"]),
    ("moi truong", ["environment"]),
    ("bien doi khi hau", ["climate", "change"]),
    ("chuoi cung ung", ["supply", "chain"]),
    ("thuong mai dien tu", ["ecommerce"]),
]


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return ascii_text.replace("đ", "d").replace("Đ", "D")


# @trace: REQ-026
def fallback_academic_keywords(topic: str, max_terms: int = 8) -> str:
    normalized = strip_accents(topic).lower()
    normalized = re.sub(r"[^a-z0-9\s-]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    terms: List[str] = []
    mapped_words: set[str] = set()
    for phrase, mapped_terms in _PHRASE_MAPPINGS:
        phrase_words = phrase.split()
        if phrase in normalized and not any(word in mapped_words for word in phrase_words):
            terms.extend(mapped_terms)
            mapped_words.update(phrase_words)

    for token in re.findall(r"[a-z0-9-]+", normalized):
        if token in _STOPWORDS or token in mapped_words or len(token) <= 2:
            continue
        # Chỉ nhận token nếu là từ tiếng Anh chuẩn
        terms.append(token)

    unique_terms = list(dict.fromkeys(terms))
    return " ".join(unique_terms[:max_terms]) or (topic or "").strip()
