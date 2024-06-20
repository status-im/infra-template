provider "cloudflare" {
  email      = data.pass_password.cloudflare_email.password
  api_key    = data.pass_password.cloudflare_token.password
}

# Uses PASSWORD_STORE_DIR environment variable
provider "pass" {}
