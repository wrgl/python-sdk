Quickstart
==========

Installation
------------

Install the package with pip:

.. code-block:: bash

    pip install wrgl

Initialization
--------------

First, create a Keycloak client authorized with scope "read" and "write" on the repository is needed. Then pass in client id and secret during initialization:

.. code-block:: python

    import os
    from wrgl import Repository

    # read access token from environment variable
    repo = Repository(
        # replace "my-repository" with wrgld host
        'https://my-repository',
        # read client id and secret from environment variable
        os.getenv('CLIENT_ID'),
        os.getenv('CLIENT_SECRET')
    )

Common operations
-----------------

.. code-block:: python

    # create a new commit
    with open('data.csv', 'rb') as f:
        result = repo.commit(
            branch='main',
            message='my commit',
            file=f,
            primary_key=['id']
        )

    print(result.sum)
    # 0cc08b02e252798ed63a0e14cc0f1bca

    # get commit with checksum
    commit = repo.get_commit(result.sum)

    # get the latest commit of branch main
    commit = repo.get_branch('main')

    # get all branches and their referenced commits
    print(repo.get_refs())
    # {'heads/main': '0cc08b02e252798ed63a0e14cc0f1bca'}

    # get the commit history of branch main, going back 10 generations
    repo.get_commit_tree('heads/main', max_depth=10)

    # download rows and save as CSV
    import csv
    with open('output.csv', 'w') as f:
        writer = csv.writer(f)
        for row in repo.get_blocks(result.sum):
            writer.writerow(row)

    # compare two commits
    diff_reader = repo.diff_reader(commit_sum1, commit_sum2)
    if diff_reader.column_changes.new_values != diff_reader.column_changes.old_values:
        print('column changes: %s' % diff_reader.column_changes)

    if diff_reader.pk_changes.new_values != diff_reader.pk_changes.old_values:
        print('pk changes: %s' % diff_reader.pk_changes)
    
    if diff_reader.added_rows is not None:
        print('%d added rows:' % len(diff_reader.added_rows))
        print('  columns: %s' % diff_reader.added_rows.columns)
        print('  primary key: %s' % diff_reader.added_rows.primary_key)
        for i, row in enumerate(diff_reader.added_rows):
            print('  row %d: %s', i, row)
            if i >= 100:
                break

        print('%d removed rows:' % len(diff_reader.removed_rows))
        print('  columns: %s' % diff_reader.removed_rows.columns)
        print('  primary key: %s' % diff_reader.removed_rows.primary_key)
        for i, row in enumerate(diff_reader.removed_rows):
            print('  row %d: %s', i, row)
            if i >= 100:
                break

        print('%d modified rows:' % len(diff_reader.modified_rows))
        print('  columns: %s' % diff_reader.modified_rows.columns)
        print('  primary key: %s' % diff_reader.modified_rows.primary_key)
        for i, row in enumerate(diff_reader.modified_rows):
            print('  row %d: %s', i, row)
            if i >= 100:
                break

