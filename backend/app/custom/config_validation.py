import json
from typing import Any

from app.shared.limits import CAMPO_CONFIGURACAO_MAX_BYTES


def validar_configuracao(
    configuracao: object,
) -> dict[str, Any]:
    if not isinstance(configuracao, dict):
        raise ValueError(
            "A configuração precisa ser um objeto JSON."
        )

    try:
        conteudo = json.dumps(
            configuracao,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError(
            "A configuração precisa conter apenas valores JSON válidos."
        ) from error

    if len(conteudo) > CAMPO_CONFIGURACAO_MAX_BYTES:
        raise ValueError(
            "A configuração serializada não pode ultrapassar "
            f"{CAMPO_CONFIGURACAO_MAX_BYTES} bytes."
        )

    return configuracao