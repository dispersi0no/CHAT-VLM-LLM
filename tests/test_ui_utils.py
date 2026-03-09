"""Tests for UI utility modules: message_renderer, components, bbox_display."""

import json
import sys
import types
from unittest.mock import MagicMock, call, patch

import pytest

from ui.message_renderer import convert_html_table_to_text, is_dots_ocr_json_response

# ---------------------------------------------------------------------------
# TestIsDotsOcrJsonResponse — pure function, no mocking needed
# ---------------------------------------------------------------------------


class TestIsDotsOcrJsonResponse:
    """Tests for is_dots_ocr_json_response pure function."""

    def test_valid_json_with_bbox_and_category_returns_true(self):
        content = '[{"bbox": [0, 0, 100, 100], "category": "text", "text": "hello"}]'
        assert is_dots_ocr_json_response(content) is True

    def test_single_element_with_bbox_and_category_returns_true(self):
        content = '[{"bbox": [10, 20, 30, 40], "category": "image"}]'
        assert is_dots_ocr_json_response(content) is True

    def test_whitespace_around_content_returns_true(self):
        content = '  [{"bbox": [0, 0, 1, 1], "category": "text"}]  '
        assert is_dots_ocr_json_response(content) is True

    def test_json_array_without_bbox_returns_false(self):
        content = '[{"category": "text", "text": "hello"}]'
        assert is_dots_ocr_json_response(content) is False

    def test_json_array_without_category_returns_false(self):
        content = '[{"bbox": [0, 0, 100, 100], "text": "hello"}]'
        assert is_dots_ocr_json_response(content) is False

    def test_empty_array_returns_false(self):
        assert is_dots_ocr_json_response("[]") is False

    def test_plain_text_returns_false(self):
        assert is_dots_ocr_json_response("Hello world") is False

    def test_starts_with_bracket_but_invalid_json_returns_false(self):
        assert is_dots_ocr_json_response("[{invalid json}]") is False

    def test_nested_objects_without_bbox_returns_false(self):
        content = '[{"data": {"nested": true}, "category": "text"}]'
        assert is_dots_ocr_json_response(content) is False

    def test_empty_string_returns_false(self):
        assert is_dots_ocr_json_response("") is False

    def test_multiple_elements_with_bbox_and_category_returns_true(self):
        content = json.dumps(
            [
                {"bbox": [0, 0, 10, 10], "category": "text", "text": "a"},
                {"bbox": [10, 10, 20, 20], "category": "image"},
            ]
        )
        assert is_dots_ocr_json_response(content) is True


# ---------------------------------------------------------------------------
# TestConvertHtmlTableToText — mostly pure (regex-based)
# ---------------------------------------------------------------------------


class TestConvertHtmlTableToText:
    """Tests for convert_html_table_to_text function."""

    def test_simple_table_extracts_cell_text_with_separator(self):
        html = "<table><tr><td>A</td><td>B</td></tr></table>"
        result = convert_html_table_to_text(html)
        assert "A | B" in result

    def test_table_with_th_headers_extracts_headers(self):
        html = "<table><tr><th>Name</th><th>Age</th></tr></table>"
        result = convert_html_table_to_text(html)
        assert "Name | Age" in result

    def test_multiple_rows(self):
        html = (
            "<table>"
            "<tr><td>A</td><td>B</td></tr>"
            "<tr><td>C</td><td>D</td></tr>"
            "</table>"
        )
        result = convert_html_table_to_text(html)
        assert "A | B" in result
        assert "C | D" in result

    def test_nested_html_tags_inside_cells_are_stripped(self):
        html = "<table><tr><td><b>Bold</b></td><td><i>Italic</i></td></tr></table>"
        result = convert_html_table_to_text(html)
        assert "Bold" in result
        assert "Italic" in result
        assert "<b>" not in result
        assert "<i>" not in result

    def test_cell_text_longer_than_30_chars_is_truncated(self):
        long_text = "x" * 50
        html = f"<table><tr><td>{long_text}</td></tr></table>"
        result = convert_html_table_to_text(html)
        assert "..." in result

    def test_content_with_no_tables_returns_unchanged(self):
        content = "No tables here, just plain text."
        result = convert_html_table_to_text(content)
        assert result == content

    def test_empty_table_handled_gracefully(self):
        html = "<table></table>"
        # Should not raise; result is a string
        result = convert_html_table_to_text(html)
        assert isinstance(result, str)

    def test_content_mixed_with_text_and_tables_preserves_non_table_text(self):
        html = "Before <table><tr><td>Cell</td></tr></table> After"
        result = convert_html_table_to_text(html)
        assert "Before" in result
        assert "After" in result
        assert "Cell" in result

    def test_cell_truncation_at_27_chars_plus_ellipsis(self):
        # 50 chars → first 27 + "..."
        long_text = "a" * 50
        html = f"<table><tr><td>{long_text}</td></tr></table>"
        result = convert_html_table_to_text(html)
        assert "a" * 27 + "..." in result


# ---------------------------------------------------------------------------
# Helpers: import Streamlit-dependent modules after st is mocked in conftest
# ---------------------------------------------------------------------------

import ui.bbox_display as bbox_display_module
import ui.components as components_module

# ---------------------------------------------------------------------------
# TestRenderMetricCard
# ---------------------------------------------------------------------------


class TestRenderMetricCard:
    """Tests for render_metric_card."""

    def test_calls_st_markdown_with_unsafe_allow_html(self):
        with patch.object(components_module.st, "markdown") as mock_md:
            components_module.render_metric_card("Title", "Value")
            mock_md.assert_called_once()
            _, kwargs = mock_md.call_args
            assert kwargs.get("unsafe_allow_html") is True

    def test_html_escapes_title_value_icon(self):
        with patch.object(components_module.st, "markdown") as mock_md:
            components_module.render_metric_card("<b>T</b>", "<b>V</b>", icon="<x>")
            rendered_html = mock_md.call_args[0][0]
            assert "&lt;b&gt;T&lt;/b&gt;" in rendered_html
            assert "&lt;b&gt;V&lt;/b&gt;" in rendered_html
            assert "&lt;x&gt;" in rendered_html

    def test_delta_included_when_provided(self):
        with patch.object(components_module.st, "markdown") as mock_md:
            components_module.render_metric_card("T", "V", delta="+5%")
            rendered_html = mock_md.call_args[0][0]
            assert "+5%" in rendered_html

    def test_delta_omitted_when_none(self):
        with patch.object(components_module.st, "markdown") as mock_md:
            components_module.render_metric_card("T", "V", delta=None)
            rendered_html = mock_md.call_args[0][0]
            assert "<p>" not in rendered_html
            assert "None" not in rendered_html

    def test_xss_attempt_in_title_is_escaped(self):
        with patch.object(components_module.st, "markdown") as mock_md:
            components_module.render_metric_card("<script>alert(1)</script>", "V")
            rendered_html = mock_md.call_args[0][0]
            assert "<script>" not in rendered_html
            assert "&lt;script&gt;" in rendered_html


# ---------------------------------------------------------------------------
# TestRenderProgressBar
# ---------------------------------------------------------------------------


class TestRenderProgressBar:
    """Tests for render_progress_bar."""

    def test_calls_st_progress_with_correct_value(self):
        col_mock = MagicMock()
        col_mock.__enter__ = MagicMock(return_value=col_mock)
        col_mock.__exit__ = MagicMock(return_value=False)
        with patch.object(
            components_module.st, "columns", return_value=[col_mock, col_mock]
        ):
            with patch.object(components_module.st, "progress") as mock_prog:
                components_module.render_progress_bar("label", 0.75)
                mock_prog.assert_called_once_with(0.75)

    def test_status_text_rendered_when_provided(self):
        col_mock = MagicMock()
        col_mock.__enter__ = MagicMock(return_value=col_mock)
        col_mock.__exit__ = MagicMock(return_value=False)
        with patch.object(
            components_module.st, "columns", return_value=[col_mock, col_mock]
        ):
            with patch.object(components_module.st, "progress"):
                with patch.object(components_module.st, "markdown") as mock_md:
                    components_module.render_progress_bar("label", 0.5, status="OK")
                    calls = [str(c) for c in mock_md.call_args_list]
                    assert any("OK" in c for c in calls)


# ---------------------------------------------------------------------------
# TestRenderAlert
# ---------------------------------------------------------------------------


class TestRenderAlert:
    """Tests for render_alert."""

    @pytest.mark.parametrize(
        "alert_type,method_name",
        [
            ("info", "info"),
            ("success", "success"),
            ("warning", "warning"),
            ("error", "error"),
        ],
    )
    def test_correct_st_method_called(self, alert_type, method_name):
        with patch.object(components_module.st, method_name) as mock_fn:
            components_module.render_alert("msg", alert_type=alert_type)
            mock_fn.assert_called_once_with("msg")

    def test_unknown_type_falls_back_to_st_info(self):
        with patch.object(components_module.st, "info") as mock_info:
            components_module.render_alert("msg", alert_type="unknown")
            mock_info.assert_called_once_with("msg")


# ---------------------------------------------------------------------------
# TestRenderFeatureList
# ---------------------------------------------------------------------------


class TestRenderFeatureList:
    """Tests for render_feature_list."""

    def test_renders_each_feature_with_checkmark(self):
        with patch.object(components_module.st, "markdown") as mock_md:
            components_module.render_feature_list(["Alpha", "Beta"])
            calls_text = [str(c) for c in mock_md.call_args_list]
            assert any("✅" in t and "Alpha" in t for t in calls_text)
            assert any("✅" in t and "Beta" in t for t in calls_text)

    def test_custom_title_used(self):
        with patch.object(components_module.st, "markdown") as mock_md:
            components_module.render_feature_list(["F"], title="My Title")
            first_call_args = mock_md.call_args_list[0][0][0]
            assert "My Title" in first_call_args


# ---------------------------------------------------------------------------
# TestRenderCodeExample
# ---------------------------------------------------------------------------


class TestRenderCodeExample:
    """Tests for render_code_example."""

    def test_calls_st_code_with_correct_language(self):
        with patch.object(components_module.st, "code") as mock_code:
            with patch.object(components_module.st, "caption"):
                components_module.render_code_example("x=1", language="python")
                mock_code.assert_called_once_with("x=1", language="python")

    def test_caption_rendered_when_provided(self):
        with patch.object(components_module.st, "code"):
            with patch.object(components_module.st, "caption") as mock_cap:
                components_module.render_code_example("x=1", caption="Example")
                mock_cap.assert_called_once_with("Example")

    def test_no_caption_st_caption_not_called(self):
        with patch.object(components_module.st, "code"):
            with patch.object(components_module.st, "caption") as mock_cap:
                components_module.render_code_example("x=1", caption=None)
                mock_cap.assert_not_called()


# ---------------------------------------------------------------------------
# TestRenderComparisonTable
# ---------------------------------------------------------------------------


class TestRenderComparisonTable:
    """Tests for render_comparison_table."""

    def test_calls_st_dataframe(self):
        df = MagicMock(name="dataframe")
        with patch.object(components_module.st, "markdown"):
            with patch.object(components_module.st, "dataframe") as mock_df:
                components_module.render_comparison_table(df, title="Test")
                mock_df.assert_called_once()
                assert mock_df.call_args[0][0] is df

    def test_title_rendered_as_markdown(self):
        df = MagicMock(name="dataframe")
        with patch.object(components_module.st, "markdown") as mock_md:
            with patch.object(components_module.st, "dataframe"):
                components_module.render_comparison_table(df, title="My Table")
                mock_md.assert_called_once()
                assert "My Table" in mock_md.call_args[0][0]


# ---------------------------------------------------------------------------
# TestRenderImagePreview
# ---------------------------------------------------------------------------


class TestRenderImagePreview:
    """Tests for render_image_preview."""

    def test_calls_st_image_with_caption(self):
        with patch.object(components_module.st, "image") as mock_img:
            components_module.render_image_preview("img_data", caption="Cap")
            mock_img.assert_called_once()
            assert mock_img.call_args[1]["caption"] == "Cap"

    def test_use_container_width_true_when_max_width_is_none(self):
        with patch.object(components_module.st, "image") as mock_img:
            components_module.render_image_preview("img_data", max_width=None)
            assert mock_img.call_args[1]["use_container_width"] is True

    def test_use_container_width_false_when_max_width_provided(self):
        with patch.object(components_module.st, "image") as mock_img:
            components_module.render_image_preview("img_data", max_width=300)
            assert mock_img.call_args[1]["use_container_width"] is False


# ---------------------------------------------------------------------------
# TestRenderTabsContent
# ---------------------------------------------------------------------------


class TestRenderTabsContent:
    """Tests for render_tabs_content."""

    def test_creates_correct_number_of_tabs(self):
        tab_mock = MagicMock()
        tab_mock.__enter__ = MagicMock(return_value=tab_mock)
        tab_mock.__exit__ = MagicMock(return_value=False)
        tabs_data = {"Tab1": "Content1", "Tab2": "Content2"}
        with patch.object(
            components_module.st, "tabs", return_value=[tab_mock, tab_mock]
        ) as mock_tabs:
            with patch.object(components_module.st, "markdown"):
                components_module.render_tabs_content(tabs_data)
                mock_tabs.assert_called_once_with(["Tab1", "Tab2"])

    def test_each_tab_gets_its_content(self):
        tab_mock = MagicMock()
        tab_mock.__enter__ = MagicMock(return_value=tab_mock)
        tab_mock.__exit__ = MagicMock(return_value=False)
        tabs_data = {"Tab1": "Content1", "Tab2": "Content2"}
        with patch.object(
            components_module.st, "tabs", return_value=[tab_mock, tab_mock]
        ):
            with patch.object(components_module.st, "markdown") as mock_md:
                components_module.render_tabs_content(tabs_data)
                rendered = [c[0][0] for c in mock_md.call_args_list]
                assert "Content1" in rendered
                assert "Content2" in rendered


# ---------------------------------------------------------------------------
# TestRenderDownloadButtons
# ---------------------------------------------------------------------------


class TestRenderDownloadButtons:
    """Tests for render_download_buttons."""

    def test_creates_correct_number_of_columns(self):
        col_mock = MagicMock()
        col_mock.__enter__ = MagicMock(return_value=col_mock)
        col_mock.__exit__ = MagicMock(return_value=False)
        data_dict = {
            "Btn1": ("data1", "file1.txt", "text/plain"),
            "Btn2": ("data2", "file2.txt", "text/plain"),
        }
        with patch.object(
            components_module.st, "columns", return_value=[col_mock, col_mock]
        ) as mock_cols:
            with patch.object(components_module.st, "download_button"):
                components_module.render_download_buttons(data_dict)
                mock_cols.assert_called_once_with(2)

    def test_each_column_gets_a_download_button(self):
        col_mock = MagicMock()
        col_mock.__enter__ = MagicMock(return_value=col_mock)
        col_mock.__exit__ = MagicMock(return_value=False)
        data_dict = {
            "Btn1": ("data1", "file1.txt", "text/plain"),
            "Btn2": ("data2", "file2.txt", "text/plain"),
        }
        with patch.object(
            components_module.st, "columns", return_value=[col_mock, col_mock]
        ):
            with patch.object(components_module.st, "download_button") as mock_btn:
                components_module.render_download_buttons(data_dict)
                assert mock_btn.call_count == 2


# ---------------------------------------------------------------------------
# TestDisplayBboxVisualizationImproved
# ---------------------------------------------------------------------------


class TestDisplayBboxVisualizationImproved:
    """Tests for display_bbox_visualization_improved."""

    def test_ocr_result_none_returns_immediately(self):
        with patch.object(bbox_display_module.st, "warning") as mock_warn:
            with patch.object(bbox_display_module.st, "image") as mock_img:
                bbox_display_module.display_bbox_visualization_improved(None)
                mock_warn.assert_not_called()
                mock_img.assert_not_called()

    def test_bbox_disabled_returns_immediately(self):
        ocr_result = {"prompt_info": {"bbox_enabled": False}}
        with patch.object(bbox_display_module.st, "warning") as mock_warn:
            with patch.object(bbox_display_module.st, "image") as mock_img:
                bbox_display_module.display_bbox_visualization_improved(ocr_result)
                mock_warn.assert_not_called()
                mock_img.assert_not_called()

    def test_missing_image_calls_st_warning(self):
        ocr_result = {
            "prompt_info": {"bbox_enabled": True},
            "image": None,
            "text": "some text",
        }
        mock_bbox_module = types.ModuleType("utils.bbox_visualizer")
        mock_bbox_module.BBoxVisualizer = MagicMock()
        with patch("importlib.reload"):
            with patch.dict(sys.modules, {"utils.bbox_visualizer": mock_bbox_module}):
                with patch.object(bbox_display_module.st, "warning") as mock_warn:
                    bbox_display_module.display_bbox_visualization_improved(ocr_result)
                    mock_warn.assert_called_once()

    def test_exception_in_visualizer_calls_st_error(self):
        fake_image = MagicMock()
        fake_image.size = (100, 100)
        ocr_result = {
            "prompt_info": {"bbox_enabled": True},
            "image": fake_image,
            "text": "response",
        }
        mock_bbox_module = types.ModuleType("utils.bbox_visualizer")
        mock_viz_cls = MagicMock(side_effect=RuntimeError("boom"))
        mock_bbox_module.BBoxVisualizer = mock_viz_cls
        with patch("importlib.reload"):
            with patch.dict(sys.modules, {"utils.bbox_visualizer": mock_bbox_module}):
                with patch.object(bbox_display_module.st, "error") as mock_err:
                    bbox_display_module.display_bbox_visualization_improved(ocr_result)
                    mock_err.assert_called_once()
                    assert "boom" in mock_err.call_args[0][0]

    def test_no_elements_found_calls_st_warning(self):
        fake_image = MagicMock()
        fake_image.size = (100, 100)
        ocr_result = {
            "prompt_info": {"bbox_enabled": True},
            "image": fake_image,
            "text": "response",
        }
        mock_visualizer = MagicMock()
        mock_visualizer.process_dots_ocr_response.return_value = (
            MagicMock(),
            None,
            [],
        )
        mock_bbox_module = types.ModuleType("utils.bbox_visualizer")
        mock_bbox_module.BBoxVisualizer = MagicMock(return_value=mock_visualizer)
        with patch("importlib.reload"):
            with patch.dict(sys.modules, {"utils.bbox_visualizer": mock_bbox_module}):
                with patch.object(bbox_display_module.st, "warning") as mock_warn:
                    with patch.object(bbox_display_module.st, "image"):
                        bbox_display_module.display_bbox_visualization_improved(
                            ocr_result
                        )
                        mock_warn.assert_called()

    def test_successful_visualization_calls_st_image_and_metric(self):
        fake_image = MagicMock()
        fake_image.size = (100, 100)
        ocr_result = {
            "prompt_info": {"bbox_enabled": True},
            "image": fake_image,
            "text": "response",
        }
        elements = [
            {"bbox": [0, 0, 10, 10], "category": "text", "text": "hello"},
        ]
        mock_visualizer = MagicMock()
        mock_visualizer.process_dots_ocr_response.return_value = (
            MagicMock(),
            MagicMock(),
            elements,
        )
        mock_visualizer.get_statistics.return_value = {
            "total_elements": 1,
            "unique_categories": 1,
        }
        mock_bbox_module = types.ModuleType("utils.bbox_visualizer")
        mock_bbox_module.BBoxVisualizer = MagicMock(return_value=mock_visualizer)
        col_mock = MagicMock()
        col_mock.__enter__ = MagicMock(return_value=col_mock)
        col_mock.__exit__ = MagicMock(return_value=False)

        def make_column_mocks(arg):
            n = len(arg) if isinstance(arg, list) else int(arg)
            return [col_mock] * n

        with patch("importlib.reload") as mock_reload:
            with patch.dict(sys.modules, {"utils.bbox_visualizer": mock_bbox_module}):
                with patch.object(bbox_display_module.st, "image") as mock_img:
                    with patch.object(bbox_display_module.st, "metric") as mock_metric:
                        with patch.object(
                            bbox_display_module.st,
                            "columns",
                            side_effect=make_column_mocks,
                        ):
                            with patch.object(bbox_display_module.st, "markdown"):
                                with patch.object(bbox_display_module.st, "divider"):
                                    with patch.object(
                                        bbox_display_module.st, "subheader"
                                    ):
                                        with patch.object(
                                            bbox_display_module.st, "caption"
                                        ):
                                            with patch.object(
                                                bbox_display_module.st, "code"
                                            ):
                                                with patch.object(
                                                    bbox_display_module.st,
                                                    "container",
                                                    return_value=col_mock,
                                                ):
                                                    bbox_display_module.display_bbox_visualization_improved(
                                                        ocr_result
                                                    )
                        assert mock_img.call_count >= 1
                        assert mock_metric.call_count >= 1
            mock_reload.assert_called_once_with(mock_bbox_module)
