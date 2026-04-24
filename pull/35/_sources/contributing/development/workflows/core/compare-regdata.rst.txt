.. _workflow_compare_regdata:

*******************
compare-regdata.yml
*******************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/compare-regdata.yml

The Regression Data Comparison workflow compares the regression data between the current branch and the base branch on pull requests. It only runs on pull requests and not on the master branch. The workflow generates regression data for the latest commit on the pull request and compares it with the master branch using the comparison notebook. The notebook is then uploaded as an artifact and pushed to reg-data-comp repository for previews in the bot comment.

.. note :: The workflow exports images from the comparison notebook and embeds them in the bot comment. Unless there are any key changes to any of the HDF files in the regression data the bot will only show two images, one containing the spectrum change and another containing relative changes in the keys. If there are any key changes, the bot will show three images, the additional one visualizing the key changes.
