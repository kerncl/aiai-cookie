variable "subscription_id" {
  description = "Azure subscription ID. azurerm v4 requires this explicitly."
  type        = string
}

variable "location" {
  description = "Azure region. southeastasia (Singapore) is nearest to Malaysia."
  type        = string
  default     = "southeastasia"
}

variable "resource_group_name" {
  description = "Resource group holding everything. Deleting it removes the lot."
  type        = string
  default     = "rg-aiai-cookie"
}

variable "environment_name" {
  description = "Container Apps environment name."
  type        = string
  default     = "aiai-env"
}

variable "log_analytics_name" {
  description = "Log Analytics workspace name. The CLI generated a random one; here we choose."
  type        = string
  default     = "law-aiai-cookie"
}

variable "app_name" {
  description = "Container app name. Becomes the first label of the public URL."
  type        = string
  default     = "aiai-cookie"
}

variable "image" {
  description = "Public image to run. Must be anonymously pullable or Azure needs registry credentials."
  type        = string
  default     = "ghcr.io/kerncl/aiai-cookie:latest"
}

variable "target_port" {
  description = "Port the container listens on. Must match EXPOSE in the Dockerfile."
  type        = number
  default     = 8000
}

variable "cpu" {
  description = "vCPU per replica. Must pair validly with memory (0.25 <-> 0.5Gi)."
  type        = number
  default     = 0.25
}

variable "memory" {
  description = "Memory per replica, with unit."
  type        = string
  default     = "0.5Gi"
}

variable "min_replicas" {
  description = "0 = scale to zero = RM 0 when idle. Set to 1 for no cold start (~RM 23/mo)."
  type        = number
  default     = 0

  validation {
    condition     = var.min_replicas >= 0 && var.min_replicas <= 2
    error_message = "Keep min_replicas at 0 for free tier, or 1 to stay warm."
  }
}

variable "max_replicas" {
  description = "Hard ceiling on concurrent replicas, and therefore on spend."
  type        = number
  default     = 2

  validation {
    condition     = var.max_replicas >= 1 && var.max_replicas <= 5
    error_message = "max_replicas above 5 risks real cost; raise deliberately."
  }
}

variable "tags" {
  description = "Tags applied to every resource. Makes orphans findable later."
  type        = map(string)
  default = {
    project    = "aiai-cookie"
    managed_by = "terraform"
    cost_tier  = "free"
  }
}
