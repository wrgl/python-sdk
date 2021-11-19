from wrgl.serialize import Serializable


class CommitResult(Serializable):
    fields = {
        'sum': str,
        'table': str,
    }


class Table(Serializable):
    fields = {
        'sum': str,
        'columns': [str],
        'pk': [int],
        'rows_count': int,
    }


class Commit(Serializable):
    fields = {
        'sum': str,
        'author_name': str,
        'author_email': str,
        'message': str,
        'table': Table,
        'time': str,
        'parents': [str],
    }


# side-step recursive class restriction
Commit.fields['parent_commits'] = {Commit}
