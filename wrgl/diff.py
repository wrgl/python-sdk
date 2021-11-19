from wrgl.serialize import Serializable


class RowDiff(Serializable):
    fields = {
        'off1': int,
        'off2': int,
    }


class DiffResponse(Serializable):
    fields = {
        "table_sum": str,
        "old_table_sum": str,
        "old_pk": [int],
        "pk": [int],
        "old_columns": [str],
        "columns": [str],
        "row_diff": [RowDiff],
    }
