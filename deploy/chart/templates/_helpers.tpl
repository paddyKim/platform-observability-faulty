{{- define "demo.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "demo.image" -}}
{{- if hasPrefix "sha256:" .tag -}}
{{ printf "%s@%s" .repository .tag }}
{{- else -}}
{{ printf "%s:%s" .repository .tag }}
{{- end -}}
{{- end -}}
