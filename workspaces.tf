/**
 * This is a hacky way of binding specific variable
 * values to different Terraform workspaces.
 *
 * Details:
 * https://github.com/hashicorp/terraform/issues/15966
 */

locals {
  env = {
    defaults = {
      /* Default settings for all fleets/workspaces. */
    }

    test = {
      /* Settings specific to the test fleet/workspace. */
    }
  }
}

/* Makes fleet settings available under local.ws. */
locals {
  ws = merge(local.env["defaults"], local.env[terraform.workspace])
}
