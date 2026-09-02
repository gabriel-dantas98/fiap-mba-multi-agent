variable "location" {
  # O lab da disciplina usa eastus2 como padrão, mas a política de regiões
  # permitidas da nossa Azure for Students só libera eastus, chilecentral,
  # brazilsouth, canadacentral e centralus (mesma restrição vista na Aula 1).
  # eastus também suporta Flex Consumption (FC1), então ficou o default aqui.
  description = "Região do Azure onde os recursos serão provisionados"
  type        = string
  default     = "eastus"
}

variable "aci_enabled" {
  description = "Quando true, provisiona o ACI 'padrão' do lab (0.5 vCPU / 1GB, restart Always). Deixe false no primeiro apply (a imagem precisa ser pushed ao ACR antes)."
  type        = bool
  default     = false
}

variable "aci_sized_enabled" {
  description = "Exercício 2.3(b) — variante right-sized do ACI (1 vCPU / 2GB) para comparar custo/hora com a variante padrão. Requer imagem já no ACR."
  type        = bool
  default     = false
}

variable "aci_job_enabled" {
  description = "Exercício 2.3(a) — variante de job batch do ACI (restart_policy = OnFailure), simulando um recálculo noturno de recomendações que roda e termina. Requer imagem já no ACR."
  type        = bool
  default     = false
}
