"""Tests for the command-line surface and the argument gates in ``convert()``.

``convert()`` validates every argument before it touches Demucs, basic-pitch or
librosa, so the whole gate is reachable from a plain clone with NumPy only.
"""

import pytest

from audio8bit import version as package_version
from audio8bit import converter as c
from audio8bit.cli import build_parser, main


class TestParser:

    def test_defaults_match_the_documented_ones(self):
        args = build_parser().parse_args(["-i", "song.mp3"])
        assert args.input == "song.mp3"
        assert args.output is None
        assert args.format is None
        assert args.source == c.DEFAULT_SOURCE
        assert args.method == c.DEFAULT_METHOD
        assert args.voices == c.DEFAULT_VOICES
        assert args.transpose == c.DEFAULT_TRANSPOSE
        assert args.bits == c.DEFAULT_BITS
        assert args.rate == c.DEFAULT_RATE
        assert args.duty == c.DEFAULT_DUTY
        assert (args.key_snap, args.arrange, args.echo, args.dither) == \
            ("on", "on", "on", "on")
        assert args.no_cache is False
        assert args.cache_dir is None

    def test_the_input_is_required(self):
        with pytest.raises(SystemExit) as excinfo:
            build_parser().parse_args([])
        assert excinfo.value.code == 2

    def test_a_non_numeric_value_is_rejected(self):
        with pytest.raises(SystemExit) as excinfo:
            build_parser().parse_args(["-i", "song.mp3", "--bits", "crunchy"])
        assert excinfo.value.code == 2

    @pytest.mark.parametrize("flag,value", [
        ("-s", "beatbox"), ("-m", "hum"), ("-V", "orchestra"),
        ("--key-snap", "maybe"), ("--arrange", "perhaps"),
        ("--echo", "loud"), ("--dither", "gritty"),
    ])
    def test_an_unknown_choice_is_rejected(self, flag, value):
        with pytest.raises(SystemExit) as excinfo:
            build_parser().parse_args(["-i", "song.mp3", flag, value])
        assert excinfo.value.code == 2

    def test_every_documented_option_parses(self):
        args = build_parser().parse_args([
            "-i", "song.mp3", "-o", "out.ogg", "-f", "ogg", "-s", "vocals",
            "-m", "pitch", "-V", "nes", "--transpose", "-3", "--bits", "4",
            "--rate", "8000", "--duty", "0.5", "--key-snap", "off",
            "--arrange", "off", "--echo", "off", "--dither", "off",
            "--no-cache", "--cache-dir", "/tmp/stems",
        ])
        assert args.output == "out.ogg"
        assert args.format == "ogg"
        assert args.transpose == -3
        assert args.bits == 4
        assert args.no_cache is True
        assert args.cache_dir == "/tmp/stems"

    def test_version_is_reported(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            build_parser().parse_args(["--version"])
        assert excinfo.value.code == 0
        assert f"audio8bit {package_version}" in capsys.readouterr().out

    def test_help_lists_the_band_and_nes_voices(self, capsys):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["--help"])
        out = capsys.readouterr().out
        assert "band" in out
        assert "nes" in out


class TestMain:

    def test_a_missing_input_is_reported_on_stderr(self, capsys):
        assert main(["-i", "no-such-file.mp3"]) == 1
        captured = capsys.readouterr()
        assert captured.err.startswith("audio8bit:")
        assert captured.out == ""

    def test_a_bad_argument_exits_with_two(self):
        with pytest.raises(SystemExit) as excinfo:
            main(["-i", "song.mp3", "--bits", "crunchy"])
        assert excinfo.value.code == 2


class TestConvertArgumentGates:
    """Every gate runs before any heavy dependency is imported."""

    @pytest.fixture
    def source(self, tmp_path):
        path = tmp_path / "song.mp3"
        path.write_bytes(b"not really audio, but it exists")
        return str(path)

    @pytest.fixture
    def gated(self, monkeypatch):
        """Stop the run right after the argument gates, wherever it is run.

        Without this the "accepted" cases would fall through to a real Demucs
        separation on a machine that has it installed.
        """

        def stop(*args, **kwargs):
            raise c.ConversionError("separation reached")

        monkeypatch.setattr(c, "separate_sources", stop)

    def test_a_missing_file_is_rejected(self):
        with pytest.raises(c.ConversionError) as excinfo:
            c.convert("definitely-not-here.mp3")
        assert "not found" in str(excinfo.value)

    @pytest.mark.parametrize("bits,accepted", [
        (1, True), (8, True), (0, False), (9, False), (-1, False),
    ])
    def test_the_bit_depth_gate(self, gated, source, bits, accepted):
        with pytest.raises(c.ConversionError) as excinfo:
            c.convert(source, bits=bits)
        message = str(excinfo.value)
        if accepted:
            assert message == "separation reached"
        else:
            assert "--bits" in message

    @pytest.mark.parametrize("transpose,accepted", [
        (-24, True), (0, True), (24, True), (25, False), (-25, False),
    ])
    def test_the_transpose_gate(self, gated, source, transpose, accepted):
        with pytest.raises(c.ConversionError) as excinfo:
            c.convert(source, transpose=transpose)
        message = str(excinfo.value)
        if accepted:
            assert message == "separation reached"
        else:
            assert "--transpose" in message

    @pytest.mark.parametrize("rate,accepted", [
        (1000, True), (44100, True), (999, False), (0, False),
    ])
    def test_the_sample_rate_gate(self, gated, source, rate, accepted):
        with pytest.raises(c.ConversionError) as excinfo:
            c.convert(source, rate=rate)
        message = str(excinfo.value)
        if accepted:
            assert message == "separation reached"
        else:
            assert "--rate" in message

    @pytest.mark.parametrize("duty,accepted", [
        (0.05, True), (0.5, True), (0.0, False), (1.0, False), (1.5, False),
    ])
    def test_the_duty_gate(self, gated, source, duty, accepted):
        with pytest.raises(c.ConversionError) as excinfo:
            c.convert(source, duty=duty)
        message = str(excinfo.value)
        if accepted:
            assert message == "separation reached"
        else:
            assert "--duty" in message

    @pytest.mark.parametrize("flag,value", [
        ("source", "beatbox"), ("method", "hum"), ("voices", "orchestra"),
    ])
    def test_the_choice_gates(self, gated, source, flag, value):
        with pytest.raises(c.ConversionError) as excinfo:
            c.convert(source, **{flag: value})
        assert f"--{flag}" in str(excinfo.value)
