import click
import python_terraform

class TerraformManager(object):
  """Running 'terraform' commands ... the Python way"""
  def __init__(self, working_dir:str, workspace:str, prefix:str=None) -> None:
      self.tf = python_terraform.Terraform(working_dir=working_dir)

      params = dict()

      if prefix:
        params.update(
          {'backend-config': f'workspace_key_prefix={prefix}'}
        )


      self.tf.init(
        no_color = python_terraform.IsFlagged,
        capture_output = 'yes',
        **params
      )

      return_code, stdout, stderr = self.tf.create_workspace(workspace=workspace)

      if return_code != 0:
        return_code, stdout, stderr = self.tf.set_workspace(workspace=workspace)


  def plan(self, **kwargs):
    if "auto_approve" in kwargs:
      del kwargs["auto_approve"]

    return_code, stdout, stderr = self.tf.plan(
      no_color = python_terraform.IsFlagged,
      capture_output = 'yes',
      detailed_exitcode=python_terraform.IsFlagged,
      compact_warnings=python_terraform.IsFlagged,
      **kwargs
    )

    changes = return_code == 2

    if changes:
      # plan has been successful, and there's a diff
      return_code = 0

    return return_code, changes

  def apply(self, **kwargs):
    auto_approve = False if 'auto_approve' not in kwargs else kwargs["auto_approve"]

    if not auto_approve:
      return_code, changes = self.plan(**kwargs)

      if changes:
        proceed = (input("OK to apply changes?") == 'yes')
        capture_output = None
        if not proceed:
          click.secho("Apply aborted, nothing has changed", bold=True)
