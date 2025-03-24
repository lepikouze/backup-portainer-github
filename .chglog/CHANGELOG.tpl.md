{{- /* Title block */ -}}
{{ if .Versions }}
{{- range .Versions }}
{{- if .Tag.Previous }}
## 📦 {{ .Tag.Name }} – {{ datetime "2006-01-02" .Tag.Date }}

[Voir les changements]({{ .Tag.CompareURL }})

{{- else }}
## 📦 {{ .Tag.Name }} – {{ datetime "2006-01-02" .Tag.Date }}
{{- end }}

{{- if .CommitGroups -}}
{{- range .CommitGroups }}
### {{ .Title }}

{{- range .Commits }}
- {{ if .Scope }}**{{ .Scope }}:** {{ end }}{{ .Subject }}
{{- end }}

{{ end -}}
{{- end -}}

{{ if .RevertCommits }}
### ⏪ Reverts

{{ range .RevertCommits }}
- {{ .Revert.Header }}
{{ end }}
{{ end }}

{{ if .MergeCommits }}
### 🔀 Merges

{{ range .MergeCommits }}
- {{ .Header }}
{{ end }}
{{ end }}

---
{{ end }}
{{ end }}