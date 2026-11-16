"""VerificationError carries the mismatch list. The message stays the sentence the caller passed."""

from prusaslicer_mcp.errors import VerificationError
from prusaslicer_mcp.verify import Mismatch, Verification


def test_verification_error_keeps_the_message_and_exposes_mismatches():
    mismatch = Mismatch("layer_height", "0.2", "0.3")
    verification = Verification(ok=False, mismatches=[mismatch])
    message = "El G-code no usa la configuración pedida (layer_height: esperado '0.2', obtenido '0.3')."

    err = VerificationError(message, verification)

    assert str(err) == message
    assert err.message == message
    assert err.verification is verification
    assert err.mismatches == [mismatch]
    assert err.mismatches is not verification.mismatches


def test_verification_error_without_a_report_has_an_empty_mismatch_list():
    err = VerificationError("fallo")

    assert str(err) == "fallo"
    assert err.verification is None
    assert err.mismatches == []
