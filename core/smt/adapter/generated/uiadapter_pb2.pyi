from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ComponentFamily(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FAMILY_UNSPECIFIED: _ClassVar[ComponentFamily]
    FAMILY_TEXT_INPUT: _ClassVar[ComponentFamily]
    FAMILY_SELECTION: _ClassVar[ComponentFamily]
    FAMILY_ACTION: _ClassVar[ComponentFamily]
    FAMILY_STRUCTURE: _ClassVar[ComponentFamily]
    FAMILY_WINDOW: _ClassVar[ComponentFamily]
    FAMILY_STATUSBAR: _ClassVar[ComponentFamily]
    FAMILY_TABLE_CONTROL: _ClassVar[ComponentFamily]
    FAMILY_ALV_GRID: _ClassVar[ComponentFamily]
    FAMILY_TREE: _ClassVar[ComponentFamily]
    FAMILY_TEXT_SHELL: _ClassVar[ComponentFamily]
    FAMILY_OTHER_SHELL: _ClassVar[ComponentFamily]
    FAMILY_LEGACY: _ClassVar[ComponentFamily]
    FAMILY_UNKNOWN: _ClassVar[ComponentFamily]

class ActionOp(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ACTION_OP_UNSPECIFIED: _ClassVar[ActionOp]
    READ: _ClassVar[ActionOp]
    SET: _ClassVar[ActionOp]
    VERIFY: _ClassVar[ActionOp]
    PRESS: _ClassVar[ActionOp]
    SELECT: _ClassVar[ActionOp]
    SEND_VKEY: _ClassVar[ActionOp]
    MENU_SELECT: _ClassVar[ActionOp]
    GRID_GET_CELL: _ClassVar[ActionOp]
    GRID_SET_CELL: _ClassVar[ActionOp]
    GRID_SELECT_ROWS: _ClassVar[ActionOp]
    GRID_SELECT_COLUMNS: _ClassVar[ActionOp]
    GRID_CURRENT_CELL: _ClassVar[ActionOp]
    GRID_DOUBLE_CLICK_CELL: _ClassVar[ActionOp]
    GRID_PRESS_TOOLBAR: _ClassVar[ActionOp]
    GRID_CONTEXT_MENU_SELECT: _ClassVar[ActionOp]
    GRID_SET_SCROLL_ROW: _ClassVar[ActionOp]
    GRID_FIND_ROW: _ClassVar[ActionOp]
    TREE_EXPAND: _ClassVar[ActionOp]
    TREE_COLLAPSE: _ClassVar[ActionOp]
    TREE_SELECT_NODE: _ClassVar[ActionOp]
    TREE_DOUBLE_CLICK: _ClassVar[ActionOp]
    TREE_CHECK_ITEM: _ClassVar[ActionOp]
    TREE_CLICK_LINK: _ClassVar[ActionOp]
    TREE_CONTEXT_MENU_SELECT: _ClassVar[ActionOp]
    TABLE_GET_CELL: _ClassVar[ActionOp]
    TABLE_SET_CELL: _ClassVar[ActionOp]
    TABLE_SELECT_ROW: _ClassVar[ActionOp]
    TABLE_FIND_ROW: _ClassVar[ActionOp]
    TABLE_CONFIGURE_LAYOUT: _ClassVar[ActionOp]
    TEXTEDIT_GET_TEXT: _ClassVar[ActionOp]
    TEXTEDIT_SET_TEXT: _ClassVar[ActionOp]
    TEXTEDIT_VERIFY_CONTAINS: _ClassVar[ActionOp]
    CALENDAR_SELECT_DATE: _ClassVar[ActionOp]
    CALENDAR_SELECT_RANGE: _ClassVar[ActionOp]
    SPLITTER_SET_SASH: _ClassVar[ActionOp]
    TAB_SELECT: _ClassVar[ActionOp]
    WINDOW_MAXIMIZE: _ClassVar[ActionOp]
    WINDOW_RESIZE: _ClassVar[ActionOp]
    WINDOW_CLOSE: _ClassVar[ActionOp]
    SCROLL_CONTAINER: _ClassVar[ActionOp]
    STATUSBAR_READ: _ClassVar[ActionOp]
    STATUSBAR_OPEN_LONG_TEXT: _ClassVar[ActionOp]
    COORDINATE_CLICK_FALLBACK: _ClassVar[ActionOp]

class UiEventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UI_EVENT_UNSPECIFIED: _ClassVar[UiEventType]
    STATUSBAR_MESSAGE: _ClassVar[UiEventType]
    MODAL_OPENED: _ClassVar[UiEventType]
    MODAL_CLOSED: _ClassVar[UiEventType]
    SCREEN_CHANGED: _ClassVar[UiEventType]
    SESSION_LOST: _ClassVar[UiEventType]
FAMILY_UNSPECIFIED: ComponentFamily
FAMILY_TEXT_INPUT: ComponentFamily
FAMILY_SELECTION: ComponentFamily
FAMILY_ACTION: ComponentFamily
FAMILY_STRUCTURE: ComponentFamily
FAMILY_WINDOW: ComponentFamily
FAMILY_STATUSBAR: ComponentFamily
FAMILY_TABLE_CONTROL: ComponentFamily
FAMILY_ALV_GRID: ComponentFamily
FAMILY_TREE: ComponentFamily
FAMILY_TEXT_SHELL: ComponentFamily
FAMILY_OTHER_SHELL: ComponentFamily
FAMILY_LEGACY: ComponentFamily
FAMILY_UNKNOWN: ComponentFamily
ACTION_OP_UNSPECIFIED: ActionOp
READ: ActionOp
SET: ActionOp
VERIFY: ActionOp
PRESS: ActionOp
SELECT: ActionOp
SEND_VKEY: ActionOp
MENU_SELECT: ActionOp
GRID_GET_CELL: ActionOp
GRID_SET_CELL: ActionOp
GRID_SELECT_ROWS: ActionOp
GRID_SELECT_COLUMNS: ActionOp
GRID_CURRENT_CELL: ActionOp
GRID_DOUBLE_CLICK_CELL: ActionOp
GRID_PRESS_TOOLBAR: ActionOp
GRID_CONTEXT_MENU_SELECT: ActionOp
GRID_SET_SCROLL_ROW: ActionOp
GRID_FIND_ROW: ActionOp
TREE_EXPAND: ActionOp
TREE_COLLAPSE: ActionOp
TREE_SELECT_NODE: ActionOp
TREE_DOUBLE_CLICK: ActionOp
TREE_CHECK_ITEM: ActionOp
TREE_CLICK_LINK: ActionOp
TREE_CONTEXT_MENU_SELECT: ActionOp
TABLE_GET_CELL: ActionOp
TABLE_SET_CELL: ActionOp
TABLE_SELECT_ROW: ActionOp
TABLE_FIND_ROW: ActionOp
TABLE_CONFIGURE_LAYOUT: ActionOp
TEXTEDIT_GET_TEXT: ActionOp
TEXTEDIT_SET_TEXT: ActionOp
TEXTEDIT_VERIFY_CONTAINS: ActionOp
CALENDAR_SELECT_DATE: ActionOp
CALENDAR_SELECT_RANGE: ActionOp
SPLITTER_SET_SASH: ActionOp
TAB_SELECT: ActionOp
WINDOW_MAXIMIZE: ActionOp
WINDOW_RESIZE: ActionOp
WINDOW_CLOSE: ActionOp
SCROLL_CONTAINER: ActionOp
STATUSBAR_READ: ActionOp
STATUSBAR_OPEN_LONG_TEXT: ActionOp
COORDINATE_CLICK_FALLBACK: ActionOp
UI_EVENT_UNSPECIFIED: UiEventType
STATUSBAR_MESSAGE: UiEventType
MODAL_OPENED: UiEventType
MODAL_CLOSED: UiEventType
SCREEN_CHANGED: UiEventType
SESSION_LOST: UiEventType

class ListConnectionsRequest(_message.Message):
    __slots__ = ("contract_version",)
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    def __init__(self, contract_version: _Optional[str] = ...) -> None: ...

class ConnectionInfo(_message.Message):
    __slots__ = ("connection_id", "description", "session_ids")
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SESSION_IDS_FIELD_NUMBER: _ClassVar[int]
    connection_id: str
    description: str
    session_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, connection_id: _Optional[str] = ..., description: _Optional[str] = ..., session_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class ConnectionList(_message.Message):
    __slots__ = ("contract_version", "connections")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    connections: _containers.RepeatedCompositeFieldContainer[ConnectionInfo]
    def __init__(self, contract_version: _Optional[str] = ..., connections: _Optional[_Iterable[_Union[ConnectionInfo, _Mapping]]] = ...) -> None: ...

class OpenSessionRequest(_message.Message):
    __slots__ = ("contract_version", "connection_id", "system_description", "client", "user", "password", "language", "masked_password")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CLIENT_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    MASKED_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    connection_id: str
    system_description: str
    client: str
    user: str
    password: str
    language: str
    masked_password: bool
    def __init__(self, contract_version: _Optional[str] = ..., connection_id: _Optional[str] = ..., system_description: _Optional[str] = ..., client: _Optional[str] = ..., user: _Optional[str] = ..., password: _Optional[str] = ..., language: _Optional[str] = ..., masked_password: _Optional[bool] = ...) -> None: ...

class SessionHandle(_message.Message):
    __slots__ = ("contract_version", "session_id")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    session_id: str
    def __init__(self, contract_version: _Optional[str] = ..., session_id: _Optional[str] = ...) -> None: ...

class Ack(_message.Message):
    __slots__ = ("contract_version", "success", "message")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    success: bool
    message: str
    def __init__(self, contract_version: _Optional[str] = ..., success: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...

class ScreenContext(_message.Message):
    __slots__ = ("system_id", "client", "user", "transaction_code", "program", "screen_number", "window_title", "window_count", "modal_stack")
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_CODE_FIELD_NUMBER: _ClassVar[int]
    PROGRAM_FIELD_NUMBER: _ClassVar[int]
    SCREEN_NUMBER_FIELD_NUMBER: _ClassVar[int]
    WINDOW_TITLE_FIELD_NUMBER: _ClassVar[int]
    WINDOW_COUNT_FIELD_NUMBER: _ClassVar[int]
    MODAL_STACK_FIELD_NUMBER: _ClassVar[int]
    system_id: str
    client: str
    user: str
    transaction_code: str
    program: str
    screen_number: str
    window_title: str
    window_count: int
    modal_stack: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, system_id: _Optional[str] = ..., client: _Optional[str] = ..., user: _Optional[str] = ..., transaction_code: _Optional[str] = ..., program: _Optional[str] = ..., screen_number: _Optional[str] = ..., window_title: _Optional[str] = ..., window_count: _Optional[int] = ..., modal_stack: _Optional[_Iterable[str]] = ...) -> None: ...

class SessionInfo(_message.Message):
    __slots__ = ("contract_version", "session_id", "context")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    session_id: str
    context: ScreenContext
    def __init__(self, contract_version: _Optional[str] = ..., session_id: _Optional[str] = ..., context: _Optional[_Union[ScreenContext, _Mapping]] = ...) -> None: ...

class ScanDepthOptions(_message.Message):
    __slots__ = ("deep_tabs", "deep_tables", "probe_f4", "whitelist_expand_ids")
    DEEP_TABS_FIELD_NUMBER: _ClassVar[int]
    DEEP_TABLES_FIELD_NUMBER: _ClassVar[int]
    PROBE_F4_FIELD_NUMBER: _ClassVar[int]
    WHITELIST_EXPAND_IDS_FIELD_NUMBER: _ClassVar[int]
    deep_tabs: bool
    deep_tables: bool
    probe_f4: bool
    whitelist_expand_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, deep_tabs: _Optional[bool] = ..., deep_tables: _Optional[bool] = ..., probe_f4: _Optional[bool] = ..., whitelist_expand_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class ScanRequest(_message.Message):
    __slots__ = ("contract_version", "session_id", "root_id", "include_modals", "depth", "delta_since_hash")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ROOT_ID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_MODALS_FIELD_NUMBER: _ClassVar[int]
    DEPTH_FIELD_NUMBER: _ClassVar[int]
    DELTA_SINCE_HASH_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    session_id: str
    root_id: str
    include_modals: bool
    depth: ScanDepthOptions
    delta_since_hash: str
    def __init__(self, contract_version: _Optional[str] = ..., session_id: _Optional[str] = ..., root_id: _Optional[str] = ..., include_modals: _Optional[bool] = ..., depth: _Optional[_Union[ScanDepthOptions, _Mapping]] = ..., delta_since_hash: _Optional[str] = ...) -> None: ...

class GridColumn(_message.Message):
    __slots__ = ("column_id", "title", "tech_name", "order", "is_fixed", "cell_type")
    COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    TECH_NAME_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    IS_FIXED_FIELD_NUMBER: _ClassVar[int]
    CELL_TYPE_FIELD_NUMBER: _ClassVar[int]
    column_id: str
    title: str
    tech_name: str
    order: int
    is_fixed: bool
    cell_type: str
    def __init__(self, column_id: _Optional[str] = ..., title: _Optional[str] = ..., tech_name: _Optional[str] = ..., order: _Optional[int] = ..., is_fixed: _Optional[bool] = ..., cell_type: _Optional[str] = ...) -> None: ...

class GridCell(_message.Message):
    __slots__ = ("column_id", "value", "cell_type", "masked")
    COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    CELL_TYPE_FIELD_NUMBER: _ClassVar[int]
    MASKED_FIELD_NUMBER: _ClassVar[int]
    column_id: str
    value: str
    cell_type: str
    masked: bool
    def __init__(self, column_id: _Optional[str] = ..., value: _Optional[str] = ..., cell_type: _Optional[str] = ..., masked: _Optional[bool] = ...) -> None: ...

class GridRow(_message.Message):
    __slots__ = ("row_index", "cells")
    ROW_INDEX_FIELD_NUMBER: _ClassVar[int]
    CELLS_FIELD_NUMBER: _ClassVar[int]
    row_index: int
    cells: _containers.RepeatedCompositeFieldContainer[GridCell]
    def __init__(self, row_index: _Optional[int] = ..., cells: _Optional[_Iterable[_Union[GridCell, _Mapping]]] = ...) -> None: ...

class ToolbarButton(_message.Message):
    __slots__ = ("id", "tooltip", "type", "enabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    TOOLTIP_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    id: str
    tooltip: str
    type: str
    enabled: bool
    def __init__(self, id: _Optional[str] = ..., tooltip: _Optional[str] = ..., type: _Optional[str] = ..., enabled: _Optional[bool] = ...) -> None: ...

class GridViewDetail(_message.Message):
    __slots__ = ("columns", "row_count", "visible_row_count", "current_cell_row", "current_cell_column_id", "selection_mode", "toolbar_buttons", "rows")
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    VISIBLE_ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENT_CELL_ROW_FIELD_NUMBER: _ClassVar[int]
    CURRENT_CELL_COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    SELECTION_MODE_FIELD_NUMBER: _ClassVar[int]
    TOOLBAR_BUTTONS_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedCompositeFieldContainer[GridColumn]
    row_count: int
    visible_row_count: int
    current_cell_row: int
    current_cell_column_id: str
    selection_mode: str
    toolbar_buttons: _containers.RepeatedCompositeFieldContainer[ToolbarButton]
    rows: _containers.RepeatedCompositeFieldContainer[GridRow]
    def __init__(self, columns: _Optional[_Iterable[_Union[GridColumn, _Mapping]]] = ..., row_count: _Optional[int] = ..., visible_row_count: _Optional[int] = ..., current_cell_row: _Optional[int] = ..., current_cell_column_id: _Optional[str] = ..., selection_mode: _Optional[str] = ..., toolbar_buttons: _Optional[_Iterable[_Union[ToolbarButton, _Mapping]]] = ..., rows: _Optional[_Iterable[_Union[GridRow, _Mapping]]] = ...) -> None: ...

class TreeNode(_message.Message):
    __slots__ = ("key", "text", "level", "item_type", "checkable", "is_link", "children")
    KEY_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    ITEM_TYPE_FIELD_NUMBER: _ClassVar[int]
    CHECKABLE_FIELD_NUMBER: _ClassVar[int]
    IS_LINK_FIELD_NUMBER: _ClassVar[int]
    CHILDREN_FIELD_NUMBER: _ClassVar[int]
    key: str
    text: str
    level: int
    item_type: str
    checkable: bool
    is_link: bool
    children: _containers.RepeatedCompositeFieldContainer[TreeNode]
    def __init__(self, key: _Optional[str] = ..., text: _Optional[str] = ..., level: _Optional[int] = ..., item_type: _Optional[str] = ..., checkable: _Optional[bool] = ..., is_link: _Optional[bool] = ..., children: _Optional[_Iterable[_Union[TreeNode, _Mapping]]] = ...) -> None: ...

class TreeDetail(_message.Message):
    __slots__ = ("tree_type", "column_names", "nodes", "context_menu_available")
    TREE_TYPE_FIELD_NUMBER: _ClassVar[int]
    COLUMN_NAMES_FIELD_NUMBER: _ClassVar[int]
    NODES_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_MENU_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    tree_type: str
    column_names: _containers.RepeatedScalarFieldContainer[str]
    nodes: _containers.RepeatedCompositeFieldContainer[TreeNode]
    context_menu_available: bool
    def __init__(self, tree_type: _Optional[str] = ..., column_names: _Optional[_Iterable[str]] = ..., nodes: _Optional[_Iterable[_Union[TreeNode, _Mapping]]] = ..., context_menu_available: _Optional[bool] = ...) -> None: ...

class MenuEntry(_message.Message):
    __slots__ = ("path", "id", "text", "enabled", "children")
    PATH_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    CHILDREN_FIELD_NUMBER: _ClassVar[int]
    path: str
    id: str
    text: str
    enabled: bool
    children: _containers.RepeatedCompositeFieldContainer[MenuEntry]
    def __init__(self, path: _Optional[str] = ..., id: _Optional[str] = ..., text: _Optional[str] = ..., enabled: _Optional[bool] = ..., children: _Optional[_Iterable[_Union[MenuEntry, _Mapping]]] = ...) -> None: ...

class ToolbarDetail(_message.Message):
    __slots__ = ("buttons", "menus")
    BUTTONS_FIELD_NUMBER: _ClassVar[int]
    MENUS_FIELD_NUMBER: _ClassVar[int]
    buttons: _containers.RepeatedCompositeFieldContainer[ToolbarButton]
    menus: _containers.RepeatedCompositeFieldContainer[MenuEntry]
    def __init__(self, buttons: _Optional[_Iterable[_Union[ToolbarButton, _Mapping]]] = ..., menus: _Optional[_Iterable[_Union[MenuEntry, _Mapping]]] = ...) -> None: ...

class TextEditDetail(_message.Message):
    __slots__ = ("full_text", "line_count")
    FULL_TEXT_FIELD_NUMBER: _ClassVar[int]
    LINE_COUNT_FIELD_NUMBER: _ClassVar[int]
    full_text: str
    line_count: int
    def __init__(self, full_text: _Optional[str] = ..., line_count: _Optional[int] = ...) -> None: ...

class HtmlViewerDetail(_message.Message):
    __slots__ = ("document_title", "url", "limited_scriptability")
    DOCUMENT_TITLE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    LIMITED_SCRIPTABILITY_FIELD_NUMBER: _ClassVar[int]
    document_title: str
    url: str
    limited_scriptability: bool
    def __init__(self, document_title: _Optional[str] = ..., url: _Optional[str] = ..., limited_scriptability: _Optional[bool] = ...) -> None: ...

class CalendarDetail(_message.Message):
    __slots__ = ("selection_start", "selection_end")
    SELECTION_START_FIELD_NUMBER: _ClassVar[int]
    SELECTION_END_FIELD_NUMBER: _ClassVar[int]
    selection_start: str
    selection_end: str
    def __init__(self, selection_start: _Optional[str] = ..., selection_end: _Optional[str] = ...) -> None: ...

class SplitterDetail(_message.Message):
    __slots__ = ("sash_position", "orientation")
    SASH_POSITION_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    sash_position: int
    orientation: str
    def __init__(self, sash_position: _Optional[int] = ..., orientation: _Optional[str] = ...) -> None: ...

class TabStripInShellDetail(_message.Message):
    __slots__ = ("tab_ids", "active_tab_id")
    TAB_IDS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_TAB_ID_FIELD_NUMBER: _ClassVar[int]
    tab_ids: _containers.RepeatedScalarFieldContainer[str]
    active_tab_id: str
    def __init__(self, tab_ids: _Optional[_Iterable[str]] = ..., active_tab_id: _Optional[str] = ...) -> None: ...

class OfficeControlDetail(_message.Message):
    __slots__ = ("kind", "metadata", "replay_limited")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    KIND_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    REPLAY_LIMITED_FIELD_NUMBER: _ClassVar[int]
    kind: str
    metadata: _containers.ScalarMap[str, str]
    replay_limited: bool
    def __init__(self, kind: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., replay_limited: _Optional[bool] = ...) -> None: ...

class RawShellDetail(_message.Message):
    __slots__ = ("properties",)
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    properties: _containers.ScalarMap[str, str]
    def __init__(self, properties: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ShellDetail(_message.Message):
    __slots__ = ("grid_view", "tree", "toolbar", "text_edit", "html_viewer", "calendar", "splitter", "tab_strip", "office_control", "raw")
    GRID_VIEW_FIELD_NUMBER: _ClassVar[int]
    TREE_FIELD_NUMBER: _ClassVar[int]
    TOOLBAR_FIELD_NUMBER: _ClassVar[int]
    TEXT_EDIT_FIELD_NUMBER: _ClassVar[int]
    HTML_VIEWER_FIELD_NUMBER: _ClassVar[int]
    CALENDAR_FIELD_NUMBER: _ClassVar[int]
    SPLITTER_FIELD_NUMBER: _ClassVar[int]
    TAB_STRIP_FIELD_NUMBER: _ClassVar[int]
    OFFICE_CONTROL_FIELD_NUMBER: _ClassVar[int]
    RAW_FIELD_NUMBER: _ClassVar[int]
    grid_view: GridViewDetail
    tree: TreeDetail
    toolbar: ToolbarDetail
    text_edit: TextEditDetail
    html_viewer: HtmlViewerDetail
    calendar: CalendarDetail
    splitter: SplitterDetail
    tab_strip: TabStripInShellDetail
    office_control: OfficeControlDetail
    raw: RawShellDetail
    def __init__(self, grid_view: _Optional[_Union[GridViewDetail, _Mapping]] = ..., tree: _Optional[_Union[TreeDetail, _Mapping]] = ..., toolbar: _Optional[_Union[ToolbarDetail, _Mapping]] = ..., text_edit: _Optional[_Union[TextEditDetail, _Mapping]] = ..., html_viewer: _Optional[_Union[HtmlViewerDetail, _Mapping]] = ..., calendar: _Optional[_Union[CalendarDetail, _Mapping]] = ..., splitter: _Optional[_Union[SplitterDetail, _Mapping]] = ..., tab_strip: _Optional[_Union[TabStripInShellDetail, _Mapping]] = ..., office_control: _Optional[_Union[OfficeControlDetail, _Mapping]] = ..., raw: _Optional[_Union[RawShellDetail, _Mapping]] = ...) -> None: ...

class TableColumn(_message.Message):
    __slots__ = ("title", "tech_name", "fixed")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    TECH_NAME_FIELD_NUMBER: _ClassVar[int]
    FIXED_FIELD_NUMBER: _ClassVar[int]
    title: str
    tech_name: str
    fixed: bool
    def __init__(self, title: _Optional[str] = ..., tech_name: _Optional[str] = ..., fixed: _Optional[bool] = ...) -> None: ...

class ScrollbarModel(_message.Message):
    __slots__ = ("position", "maximum", "page_size")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    MAXIMUM_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    position: int
    maximum: int
    page_size: int
    def __init__(self, position: _Optional[int] = ..., maximum: _Optional[int] = ..., page_size: _Optional[int] = ...) -> None: ...

class TableControlDetail(_message.Message):
    __slots__ = ("columns", "row_count", "visible_row_count", "vertical_scrollbar")
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    VISIBLE_ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    VERTICAL_SCROLLBAR_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedCompositeFieldContainer[TableColumn]
    row_count: int
    visible_row_count: int
    vertical_scrollbar: ScrollbarModel
    def __init__(self, columns: _Optional[_Iterable[_Union[TableColumn, _Mapping]]] = ..., row_count: _Optional[int] = ..., visible_row_count: _Optional[int] = ..., vertical_scrollbar: _Optional[_Union[ScrollbarModel, _Mapping]] = ...) -> None: ...

class MenuDetail(_message.Message):
    __slots__ = ("entries",)
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[MenuEntry]
    def __init__(self, entries: _Optional[_Iterable[_Union[MenuEntry, _Mapping]]] = ...) -> None: ...

class ComponentNode(_message.Message):
    __slots__ = ("id", "type", "type_as_number", "sub_type", "family", "name", "text", "tooltip", "default_tooltip", "icon_name", "screen_left", "screen_top", "width", "height", "changeable", "modified", "is_container", "masked", "children", "shell_detail", "table_detail", "menu_detail", "raw_properties", "unmapped", "coverage_status")
    class RawPropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TYPE_AS_NUMBER_FIELD_NUMBER: _ClassVar[int]
    SUB_TYPE_FIELD_NUMBER: _ClassVar[int]
    FAMILY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TOOLTIP_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_TOOLTIP_FIELD_NUMBER: _ClassVar[int]
    ICON_NAME_FIELD_NUMBER: _ClassVar[int]
    SCREEN_LEFT_FIELD_NUMBER: _ClassVar[int]
    SCREEN_TOP_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    CHANGEABLE_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_FIELD_NUMBER: _ClassVar[int]
    IS_CONTAINER_FIELD_NUMBER: _ClassVar[int]
    MASKED_FIELD_NUMBER: _ClassVar[int]
    CHILDREN_FIELD_NUMBER: _ClassVar[int]
    SHELL_DETAIL_FIELD_NUMBER: _ClassVar[int]
    TABLE_DETAIL_FIELD_NUMBER: _ClassVar[int]
    MENU_DETAIL_FIELD_NUMBER: _ClassVar[int]
    RAW_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    UNMAPPED_FIELD_NUMBER: _ClassVar[int]
    COVERAGE_STATUS_FIELD_NUMBER: _ClassVar[int]
    id: str
    type: str
    type_as_number: int
    sub_type: str
    family: ComponentFamily
    name: str
    text: str
    tooltip: str
    default_tooltip: str
    icon_name: str
    screen_left: int
    screen_top: int
    width: int
    height: int
    changeable: bool
    modified: bool
    is_container: bool
    masked: bool
    children: _containers.RepeatedCompositeFieldContainer[ComponentNode]
    shell_detail: ShellDetail
    table_detail: TableControlDetail
    menu_detail: MenuDetail
    raw_properties: _containers.ScalarMap[str, str]
    unmapped: bool
    coverage_status: str
    def __init__(self, id: _Optional[str] = ..., type: _Optional[str] = ..., type_as_number: _Optional[int] = ..., sub_type: _Optional[str] = ..., family: _Optional[_Union[ComponentFamily, str]] = ..., name: _Optional[str] = ..., text: _Optional[str] = ..., tooltip: _Optional[str] = ..., default_tooltip: _Optional[str] = ..., icon_name: _Optional[str] = ..., screen_left: _Optional[int] = ..., screen_top: _Optional[int] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., changeable: _Optional[bool] = ..., modified: _Optional[bool] = ..., is_container: _Optional[bool] = ..., masked: _Optional[bool] = ..., children: _Optional[_Iterable[_Union[ComponentNode, _Mapping]]] = ..., shell_detail: _Optional[_Union[ShellDetail, _Mapping]] = ..., table_detail: _Optional[_Union[TableControlDetail, _Mapping]] = ..., menu_detail: _Optional[_Union[MenuDetail, _Mapping]] = ..., raw_properties: _Optional[_Mapping[str, str]] = ..., unmapped: _Optional[bool] = ..., coverage_status: _Optional[str] = ...) -> None: ...

class ScreenSnapshot(_message.Message):
    __slots__ = ("contract_version", "session_id", "context", "root", "snapshot_hash", "captured_at_epoch_ms", "unmapped_component_ids")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    ROOT_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_HASH_FIELD_NUMBER: _ClassVar[int]
    CAPTURED_AT_EPOCH_MS_FIELD_NUMBER: _ClassVar[int]
    UNMAPPED_COMPONENT_IDS_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    session_id: str
    context: ScreenContext
    root: ComponentNode
    snapshot_hash: str
    captured_at_epoch_ms: int
    unmapped_component_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, contract_version: _Optional[str] = ..., session_id: _Optional[str] = ..., context: _Optional[_Union[ScreenContext, _Mapping]] = ..., root: _Optional[_Union[ComponentNode, _Mapping]] = ..., snapshot_hash: _Optional[str] = ..., captured_at_epoch_ms: _Optional[int] = ..., unmapped_component_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class ActionParams(_message.Message):
    __slots__ = ("text_value", "key_value", "visible_text_value", "vkey", "menu_path", "row", "column_id", "rows", "column_ids", "node_key", "item_id", "context_menu_item_id", "toolbar_button_id", "predicate_column_id", "predicate_value", "date_value", "date_range_end", "sash_position", "tab_id", "verify_masked", "comparator", "expected_value", "numeric_tolerance", "extra")
    class ExtraEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TEXT_VALUE_FIELD_NUMBER: _ClassVar[int]
    KEY_VALUE_FIELD_NUMBER: _ClassVar[int]
    VISIBLE_TEXT_VALUE_FIELD_NUMBER: _ClassVar[int]
    VKEY_FIELD_NUMBER: _ClassVar[int]
    MENU_PATH_FIELD_NUMBER: _ClassVar[int]
    ROW_FIELD_NUMBER: _ClassVar[int]
    COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    COLUMN_IDS_FIELD_NUMBER: _ClassVar[int]
    NODE_KEY_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_MENU_ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    TOOLBAR_BUTTON_ID_FIELD_NUMBER: _ClassVar[int]
    PREDICATE_COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    PREDICATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    DATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    DATE_RANGE_END_FIELD_NUMBER: _ClassVar[int]
    SASH_POSITION_FIELD_NUMBER: _ClassVar[int]
    TAB_ID_FIELD_NUMBER: _ClassVar[int]
    VERIFY_MASKED_FIELD_NUMBER: _ClassVar[int]
    COMPARATOR_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_VALUE_FIELD_NUMBER: _ClassVar[int]
    NUMERIC_TOLERANCE_FIELD_NUMBER: _ClassVar[int]
    EXTRA_FIELD_NUMBER: _ClassVar[int]
    text_value: str
    key_value: str
    visible_text_value: str
    vkey: str
    menu_path: str
    row: int
    column_id: str
    rows: _containers.RepeatedScalarFieldContainer[int]
    column_ids: _containers.RepeatedScalarFieldContainer[str]
    node_key: str
    item_id: str
    context_menu_item_id: str
    toolbar_button_id: str
    predicate_column_id: str
    predicate_value: str
    date_value: str
    date_range_end: str
    sash_position: int
    tab_id: str
    verify_masked: bool
    comparator: str
    expected_value: str
    numeric_tolerance: float
    extra: _containers.ScalarMap[str, str]
    def __init__(self, text_value: _Optional[str] = ..., key_value: _Optional[str] = ..., visible_text_value: _Optional[str] = ..., vkey: _Optional[str] = ..., menu_path: _Optional[str] = ..., row: _Optional[int] = ..., column_id: _Optional[str] = ..., rows: _Optional[_Iterable[int]] = ..., column_ids: _Optional[_Iterable[str]] = ..., node_key: _Optional[str] = ..., item_id: _Optional[str] = ..., context_menu_item_id: _Optional[str] = ..., toolbar_button_id: _Optional[str] = ..., predicate_column_id: _Optional[str] = ..., predicate_value: _Optional[str] = ..., date_value: _Optional[str] = ..., date_range_end: _Optional[str] = ..., sash_position: _Optional[int] = ..., tab_id: _Optional[str] = ..., verify_masked: _Optional[bool] = ..., comparator: _Optional[str] = ..., expected_value: _Optional[str] = ..., numeric_tolerance: _Optional[float] = ..., extra: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ActionRequest(_message.Message):
    __slots__ = ("contract_version", "session_id", "component_id", "op", "params", "allow_fragile_fallback")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    COMPONENT_ID_FIELD_NUMBER: _ClassVar[int]
    OP_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_FRAGILE_FALLBACK_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    session_id: str
    component_id: str
    op: ActionOp
    params: ActionParams
    allow_fragile_fallback: bool
    def __init__(self, contract_version: _Optional[str] = ..., session_id: _Optional[str] = ..., component_id: _Optional[str] = ..., op: _Optional[_Union[ActionOp, str]] = ..., params: _Optional[_Union[ActionParams, _Mapping]] = ..., allow_fragile_fallback: _Optional[bool] = ...) -> None: ...

class StatusbarMessage(_message.Message):
    __slots__ = ("type", "text", "message_id", "message_number")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    type: str
    text: str
    message_id: str
    message_number: str
    def __init__(self, type: _Optional[str] = ..., text: _Optional[str] = ..., message_id: _Optional[str] = ..., message_number: _Optional[str] = ...) -> None: ...

class ScreenChangeInfo(_message.Message):
    __slots__ = ("changed", "old_tcode", "new_tcode", "old_screen", "new_screen", "modal_opened", "modal_closed")
    CHANGED_FIELD_NUMBER: _ClassVar[int]
    OLD_TCODE_FIELD_NUMBER: _ClassVar[int]
    NEW_TCODE_FIELD_NUMBER: _ClassVar[int]
    OLD_SCREEN_FIELD_NUMBER: _ClassVar[int]
    NEW_SCREEN_FIELD_NUMBER: _ClassVar[int]
    MODAL_OPENED_FIELD_NUMBER: _ClassVar[int]
    MODAL_CLOSED_FIELD_NUMBER: _ClassVar[int]
    changed: bool
    old_tcode: str
    new_tcode: str
    old_screen: str
    new_screen: str
    modal_opened: bool
    modal_closed: bool
    def __init__(self, changed: _Optional[bool] = ..., old_tcode: _Optional[str] = ..., new_tcode: _Optional[str] = ..., old_screen: _Optional[str] = ..., new_screen: _Optional[str] = ..., modal_opened: _Optional[bool] = ..., modal_closed: _Optional[bool] = ...) -> None: ...

class PopupHandled(_message.Message):
    __slots__ = ("window_title", "handler_name", "action_taken")
    WINDOW_TITLE_FIELD_NUMBER: _ClassVar[int]
    HANDLER_NAME_FIELD_NUMBER: _ClassVar[int]
    ACTION_TAKEN_FIELD_NUMBER: _ClassVar[int]
    window_title: str
    handler_name: str
    action_taken: str
    def __init__(self, window_title: _Optional[str] = ..., handler_name: _Optional[str] = ..., action_taken: _Optional[str] = ...) -> None: ...

class ActionResult(_message.Message):
    __slots__ = ("contract_version", "success", "error_message", "actual_value", "masked", "statusbar_deltas", "screen_change", "elapsed_ms", "screenshot_before", "screenshot_after", "fragile", "unsupported_reason", "popups_handled")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_VALUE_FIELD_NUMBER: _ClassVar[int]
    MASKED_FIELD_NUMBER: _ClassVar[int]
    STATUSBAR_DELTAS_FIELD_NUMBER: _ClassVar[int]
    SCREEN_CHANGE_FIELD_NUMBER: _ClassVar[int]
    ELAPSED_MS_FIELD_NUMBER: _ClassVar[int]
    SCREENSHOT_BEFORE_FIELD_NUMBER: _ClassVar[int]
    SCREENSHOT_AFTER_FIELD_NUMBER: _ClassVar[int]
    FRAGILE_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_REASON_FIELD_NUMBER: _ClassVar[int]
    POPUPS_HANDLED_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    success: bool
    error_message: str
    actual_value: str
    masked: bool
    statusbar_deltas: _containers.RepeatedCompositeFieldContainer[StatusbarMessage]
    screen_change: ScreenChangeInfo
    elapsed_ms: int
    screenshot_before: ImageBlob
    screenshot_after: ImageBlob
    fragile: bool
    unsupported_reason: str
    popups_handled: _containers.RepeatedCompositeFieldContainer[PopupHandled]
    def __init__(self, contract_version: _Optional[str] = ..., success: _Optional[bool] = ..., error_message: _Optional[str] = ..., actual_value: _Optional[str] = ..., masked: _Optional[bool] = ..., statusbar_deltas: _Optional[_Iterable[_Union[StatusbarMessage, _Mapping]]] = ..., screen_change: _Optional[_Union[ScreenChangeInfo, _Mapping]] = ..., elapsed_ms: _Optional[int] = ..., screenshot_before: _Optional[_Union[ImageBlob, _Mapping]] = ..., screenshot_after: _Optional[_Union[ImageBlob, _Mapping]] = ..., fragile: _Optional[bool] = ..., unsupported_reason: _Optional[str] = ..., popups_handled: _Optional[_Iterable[_Union[PopupHandled, _Mapping]]] = ...) -> None: ...

class ActionBatch(_message.Message):
    __slots__ = ("contract_version", "session_id", "steps", "fail_fast")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STEPS_FIELD_NUMBER: _ClassVar[int]
    FAIL_FAST_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    session_id: str
    steps: _containers.RepeatedCompositeFieldContainer[ActionRequest]
    fail_fast: bool
    def __init__(self, contract_version: _Optional[str] = ..., session_id: _Optional[str] = ..., steps: _Optional[_Iterable[_Union[ActionRequest, _Mapping]]] = ..., fail_fast: _Optional[bool] = ...) -> None: ...

class RelativePosition(_message.Message):
    __slots__ = ("left", "top", "anchor_component_id")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    TOP_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_COMPONENT_ID_FIELD_NUMBER: _ClassVar[int]
    left: int
    top: int
    anchor_component_id: str
    def __init__(self, left: _Optional[int] = ..., top: _Optional[int] = ..., anchor_component_id: _Optional[str] = ...) -> None: ...

class LocatorFingerprint(_message.Message):
    __slots__ = ("exact_id", "structural_pattern", "tech_field_name", "label_text", "component_type", "sub_type", "tab_context", "screen_context", "relative_position")
    EXACT_ID_FIELD_NUMBER: _ClassVar[int]
    STRUCTURAL_PATTERN_FIELD_NUMBER: _ClassVar[int]
    TECH_FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    LABEL_TEXT_FIELD_NUMBER: _ClassVar[int]
    COMPONENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    SUB_TYPE_FIELD_NUMBER: _ClassVar[int]
    TAB_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    SCREEN_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    RELATIVE_POSITION_FIELD_NUMBER: _ClassVar[int]
    exact_id: str
    structural_pattern: str
    tech_field_name: str
    label_text: str
    component_type: str
    sub_type: str
    tab_context: str
    screen_context: str
    relative_position: RelativePosition
    def __init__(self, exact_id: _Optional[str] = ..., structural_pattern: _Optional[str] = ..., tech_field_name: _Optional[str] = ..., label_text: _Optional[str] = ..., component_type: _Optional[str] = ..., sub_type: _Optional[str] = ..., tab_context: _Optional[str] = ..., screen_context: _Optional[str] = ..., relative_position: _Optional[_Union[RelativePosition, _Mapping]] = ...) -> None: ...

class LocatorRequest(_message.Message):
    __slots__ = ("contract_version", "session_id", "fingerprint", "max_candidates")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    FINGERPRINT_FIELD_NUMBER: _ClassVar[int]
    MAX_CANDIDATES_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    session_id: str
    fingerprint: LocatorFingerprint
    max_candidates: int
    def __init__(self, contract_version: _Optional[str] = ..., session_id: _Optional[str] = ..., fingerprint: _Optional[_Union[LocatorFingerprint, _Mapping]] = ..., max_candidates: _Optional[int] = ...) -> None: ...

class LocatorCandidate(_message.Message):
    __slots__ = ("component_id", "score", "strategy", "rationale")
    COMPONENT_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_FIELD_NUMBER: _ClassVar[int]
    RATIONALE_FIELD_NUMBER: _ClassVar[int]
    component_id: str
    score: float
    strategy: str
    rationale: str
    def __init__(self, component_id: _Optional[str] = ..., score: _Optional[float] = ..., strategy: _Optional[str] = ..., rationale: _Optional[str] = ...) -> None: ...

class LocatorCandidates(_message.Message):
    __slots__ = ("contract_version", "candidates")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    CANDIDATES_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    candidates: _containers.RepeatedCompositeFieldContainer[LocatorCandidate]
    def __init__(self, contract_version: _Optional[str] = ..., candidates: _Optional[_Iterable[_Union[LocatorCandidate, _Mapping]]] = ...) -> None: ...

class UiEvent(_message.Message):
    __slots__ = ("contract_version", "session_id", "type", "statusbar", "modal_window_title", "screen_change", "message")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    STATUSBAR_FIELD_NUMBER: _ClassVar[int]
    MODAL_WINDOW_TITLE_FIELD_NUMBER: _ClassVar[int]
    SCREEN_CHANGE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    session_id: str
    type: UiEventType
    statusbar: StatusbarMessage
    modal_window_title: str
    screen_change: ScreenChangeInfo
    message: str
    def __init__(self, contract_version: _Optional[str] = ..., session_id: _Optional[str] = ..., type: _Optional[_Union[UiEventType, str]] = ..., statusbar: _Optional[_Union[StatusbarMessage, _Mapping]] = ..., modal_window_title: _Optional[str] = ..., screen_change: _Optional[_Union[ScreenChangeInfo, _Mapping]] = ..., message: _Optional[str] = ...) -> None: ...

class CaptureRequest(_message.Message):
    __slots__ = ("contract_version", "session_id", "component_id")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    COMPONENT_ID_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    session_id: str
    component_id: str
    def __init__(self, contract_version: _Optional[str] = ..., session_id: _Optional[str] = ..., component_id: _Optional[str] = ...) -> None: ...

class ImageBlob(_message.Message):
    __slots__ = ("data", "format", "width", "height")
    DATA_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    format: str
    width: int
    height: int
    def __init__(self, data: _Optional[bytes] = ..., format: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ...) -> None: ...

class OkCodeHistory(_message.Message):
    __slots__ = ("contract_version", "ok_codes")
    CONTRACT_VERSION_FIELD_NUMBER: _ClassVar[int]
    OK_CODES_FIELD_NUMBER: _ClassVar[int]
    contract_version: str
    ok_codes: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, contract_version: _Optional[str] = ..., ok_codes: _Optional[_Iterable[str]] = ...) -> None: ...
