import re
from pathlib import Path

import pytest

from prusaslicer_mcp import install as inst
from prusaslicer_mcp.errors import SlicerNotFoundError


def _fake_install_dir(tmp_path: Path) -> Path:
    d = tmp_path / "PrusaSlicer"
    d.mkdir()
    for name in ("prusa-slicer-console.exe", "prusa-slicer.exe", "prusa-gcodeviewer.exe"):
        (d / name).write_bytes(b"")
    (d / "resources").mkdir()
    return d


@pytest.fixture
def fake_version(monkeypatch):
    monkeypatch.setattr(inst, "_read_version", lambda console: "2.9.4")
    monkeypatch.setattr(inst.sys, "platform", "win32")


def test_override_dir_with_fake_exe(tmp_path, fake_version):
    d = _fake_install_dir(tmp_path)
    found = inst.find_installation(d)
    assert found.console == d / "prusa-slicer-console.exe"
    assert found.gui == d / "prusa-slicer.exe"
    assert found.gcodeviewer == d / "prusa-gcodeviewer.exe"
    assert found.resources == d / "resources"
    assert found.version == "2.9.4"


def test_env_var_used(tmp_path, fake_version, monkeypatch):
    d = _fake_install_dir(tmp_path)
    monkeypatch.setenv("PRUSASLICER_PATH", str(d))
    assert inst.find_installation().console == d / "prusa-slicer-console.exe"


def test_not_found_raises(tmp_path, fake_version, monkeypatch):
    monkeypatch.delenv("PRUSASLICER_PATH", raising=False)
    monkeypatch.setattr(inst, "candidate_dirs", lambda: [tmp_path / "nope"])
    with pytest.raises(SlicerNotFoundError) as e:
        inst.find_installation()
    assert "PRUSASLICER_PATH" in e.value.message


def test_is_supported_version():
    assert inst.is_supported_version("2.9.4")
    assert inst.is_supported_version("2.9.6")
    assert not inst.is_supported_version("2.8.1")


def test_macos_bundle_resources(tmp_path, monkeypatch):
    """macOS keeps profiles in Contents/Resources, not next to the binary."""
    macos = tmp_path / "X.app" / "Contents" / "MacOS"
    macos.mkdir(parents=True)
    (macos / "PrusaSlicer").write_bytes(b"")
    profiles = tmp_path / "X.app" / "Contents" / "Resources" / "profiles"
    profiles.mkdir(parents=True)
    monkeypatch.setattr(inst.sys, "platform", "darwin")
    monkeypatch.setattr(inst, "_read_version", lambda console: "2.9.7")
    found = inst.find_installation(macos)
    assert found.console == macos / "PrusaSlicer"
    assert found.resources == macos.parent / "Resources"
    assert (found.resources / "profiles").is_dir()


def test_lowercase_resources_still_wins(tmp_path, monkeypatch):
    """A `resources` directory beside the binary stays the one that is used."""
    d = tmp_path / "PrusaSlicer"
    d.mkdir()
    (d / "prusa-slicer").write_bytes(b"")
    (d / "resources").mkdir()
    (d.parent / "Resources").mkdir()
    monkeypatch.setattr(inst.sys, "platform", "linux")
    monkeypatch.setattr(inst, "_read_version", lambda console: "2.9.7")
    found = inst.find_installation(d)
    assert found.resources == d / "resources"


@pytest.mark.slicer
def test_real_install_version(install):
    assert re.match(r"^\d+\.\d+\.\d+", install.version)
    assert install.console.exists()


@pytest.mark.real_slicer
def test_real_install_discovers_bundle_resources(install):
    bundle = install.console.resolve().parent.parent / "Resources"
    if not bundle.is_dir():
        pytest.skip("this install is not a macOS app bundle")
    assert install.resources == bundle
    assert (install.resources / "profiles").is_dir()
