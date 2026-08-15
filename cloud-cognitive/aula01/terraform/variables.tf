variable "subscription_id" {
  description = "ID da assinatura Azure."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.subscription_id))
    error_message = "subscription_id deve ser um UUID válido."
  }
}

variable "meu_ip" {
  description = "IPv4 público autorizado no SSH (sem /32)."
  type        = string

  validation {
    condition     = can(cidrnetmask("${var.meu_ip}/32"))
    error_message = "meu_ip deve ser um endereço IPv4 válido, sem máscara CIDR."
  }
}

variable "ssh_public_key" {
  description = "Chave pública SSH do admin."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521)) ", trimspace(var.ssh_public_key)))
    error_message = "ssh_public_key deve conter uma chave pública OpenSSH válida."
  }
}

variable "location" {
  description = "Região Azure (policy Students)."
  type        = string
  default     = "chilecentral"
}

variable "resource_group_name" {
  description = "Nome do Resource Group."
  type        = string
  default     = "rg-cloud-cognitive-aula01"
}

variable "vm_size" {
  description = "SKU da VM."
  type        = string
  default     = "Standard_B2als_v2"
}

variable "admin_username" {
  description = "Usuário admin da VM."
  type        = string
  default     = "azureuser"
}
