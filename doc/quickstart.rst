:github_url: https://github.com/wrgl/python-sdk/blob/main/doc/quickstart.rst

Quickstart
==========

Installation
------------

Install the package with pip:

.. code-block:: bash

    pip install wrgl

Initialization
--------------

There are two ways to initialize:

- If you already have an access token:

.. code-block:: python

   import os
   from wrgl import Repository

   # read access token from environment variable
   repo = Repository('https://my-repository', os.getenv('REPO_ACCESS_TOKEN'))

- If you have email/password and want to authenticate with that and/or want to acquite an access token:

.. code-block:: python

   from wrgl import Repository

   repo = Repository('https://my-repository')
   token = repo.authenticate('my-email@domain.com', 'password')

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
       for row in repo.get_blocks(commit.table.sum):
           writer.writerow(row)

   # compare two commits
   diff_result = repo.diff(commit_sum1, commit_sum2)
   if diff_result.columns != diff_result.old_columns:
       print('there are column changes')
   if diff_result.primary_key != diff_result.old_primary_key:
       print('there are primary key changes')
   elif diff_result.row_diff is not None:
       # get added rows
       added_rows = repo.get_rows(table_sum1, [
           r.off1 for r in diff_result.row_diff
           if r.off2 is None
       ][:100])

       # get removed rows
       removed_rows = repo.get_rows(table_sum2, [
           r.off2 for r in diff_result.row_diff
           if r.off1 is None
       ][:100])

       # get modified rows
       modified_rows_old = repo.get_rows(table_sum1, [
           r.off1 for r in diff_result.row_diff
           if r.off1 is not None and r.off2 is not None
       ][:100])
       modified_rows_new = repo.get_rows(table_sum2, [
           r.off2 for r in diff_result.row_diff
           if r.off1 is not None and r.off2 is not None
       ][:100])

