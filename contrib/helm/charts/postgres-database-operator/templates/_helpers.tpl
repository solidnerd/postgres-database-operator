{{/*
Create a space-separated string from a list of names
*/}}
{{- define "cloudsql.instancelist" -}}
{{- $list := .Values.cloudsql.connections -}}
{{- $result := list -}}
{{- range $item := $list -}}
  {{- $result = append $result $item.name -}}
{{- end -}}
{{- join " " $result -}}
{{- end -}}
