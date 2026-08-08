from watch import process_entry


class TestProcessEntry:
    def test_prefers_folder_title_over_lowercase_file_title(self, tmp_path):
        entry = tmp_path / "downloads" / "King.of.the.Hill.S15E08.1080p.WEB.H264-CAKES"
        entry.mkdir(parents=True)
        video = entry / "king.of.the.hill.s15e08.1080p.web.h264-cakes.mkv"
        video.write_bytes(b"0" * 10)
        tv_root = tmp_path / "tv"

        process_entry(entry, tv_root=tv_root, min_size_mb=0)

        linked = list(tv_root.rglob("*.mkv"))
        assert linked == [tv_root / "King of the Hill" / "Season 15" / "King of the Hill - S15E08.mkv"]

    def test_single_file_entry_uses_its_own_title(self, tmp_path):
        entry = tmp_path / "downloads" / "Knives Out 2019 1080p BluRay HEVC x265 5.1 BONE.mkv"
        entry.parent.mkdir(parents=True)
        entry.write_bytes(b"0" * 10)
        movies_root = tmp_path / "movies"

        process_entry(entry, movies_root=movies_root, min_size_mb=0)

        linked = list(movies_root.rglob("*.mkv"))
        assert linked == [movies_root / "Knives Out (2019)" / "Knives Out (2019).mkv"]

    def test_nonexistent_path_is_a_noop(self, tmp_path):
        process_entry(tmp_path / "does-not-exist")
