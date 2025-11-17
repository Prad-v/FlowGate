package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"

	"github.com/open-telemetry/opamp-go/protobufs"
	"google.golang.org/protobuf/proto"
)

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// ParseRequest represents a request to parse an OpAMP message
type ParseRequest struct {
	Data []byte `json:"data"`
}

// ParseResponse represents the parsed message
type ParseResponse struct {
	Success bool                   `json:"success"`
	Error   string                 `json:"error,omitempty"`
	Message map[string]interface{} `json:"message,omitempty"`
}

func main() {
	mode := flag.String("mode", "parse", "Operation mode: parse, serialize")
	flag.Parse()

	switch *mode {
	case "parse":
		parseMode()
	case "serialize":
		serializeMode()
	default:
		fmt.Fprintf(os.Stderr, "Unknown mode: %s\n", *mode)
		os.Exit(1)
	}
}

func parseMode() {
	// Read input from stdin
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		respondError(fmt.Sprintf("Failed to read input: %v", err))
		return
	}

	if len(data) == 0 {
		respondError("Empty input")
		return
	}

	// Try to parse as AgentToServer message
	agentMsg := &protobufs.AgentToServer{}
	if err := proto.Unmarshal(data, agentMsg); err != nil {
		// Log detailed error for debugging
		fmt.Fprintf(os.Stderr, "Protobuf unmarshal error: %v\n", err)
		fmt.Fprintf(os.Stderr, "Message size: %d bytes\n", len(data))
		if len(data) > 0 {
			fmt.Fprintf(os.Stderr, "First 20 bytes (hex): %x\n", data[:min(20, len(data))])
		}
		respondError(fmt.Sprintf("Failed to parse AgentToServer: %v", err))
		return
	}

	// Convert to JSON-serializable format
	message := agentToServerToMap(agentMsg)

	respondSuccess(message)
}

func serializeMode() {
	// Read JSON from stdin
	var req struct {
		Message map[string]interface{} `json:"message"`
	}

	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		respondError(fmt.Sprintf("Failed to read input: %v", err))
		return
	}

	if err := json.Unmarshal(data, &req); err != nil {
		respondError(fmt.Sprintf("Failed to parse JSON: %v", err))
		return
	}

	// Convert map to ServerToAgent message
	serverMsg, err := mapToServerToAgent(req.Message)
	if err != nil {
		respondError(fmt.Sprintf("Failed to convert to ServerToAgent: %v", err))
		return
	}

	// Serialize to protobuf
	output, err := proto.Marshal(serverMsg)
	if err != nil {
		respondError(fmt.Sprintf("Failed to serialize: %v", err))
		return
	}

	// Write binary output to stdout
	os.Stdout.Write(output)
}

func agentToServerToMap(msg *protobufs.AgentToServer) map[string]interface{} {
	result := make(map[string]interface{})

	if msg.InstanceUid != "" {
		// InstanceUid is string in Go protobuf, but we need bytes for Python
		// Convert to bytes for consistency with Python protobuf
		result["instance_uid"] = []byte(msg.InstanceUid)
	}
	if msg.SequenceNum != 0 {
		result["sequence_num"] = msg.SequenceNum
	}
	if msg.Capabilities != 0 {
		result["capabilities"] = msg.Capabilities
	}
	if msg.Flags != 0 {
		result["flags"] = msg.Flags
	}

	// Agent description
	if msg.AgentDescription != nil {
		result["agent_description"] = agentDescriptionToMap(msg.AgentDescription)
	}

	// Health
	if msg.Health != nil {
		result["health"] = componentHealthToMap(msg.Health)
	}

	// Effective config
	if msg.EffectiveConfig != nil {
		result["effective_config"] = effectiveConfigToMap(msg.EffectiveConfig)
	}

	// Remote config status
	if msg.RemoteConfigStatus != nil {
		result["remote_config_status"] = remoteConfigStatusToMap(msg.RemoteConfigStatus)
	}

	// Package statuses
	if msg.PackageStatuses != nil {
		result["package_statuses"] = packageStatusesToMap(msg.PackageStatuses)
	}

	// Available components (field 14) - skip for now
	// The field name in Go protobuf may differ, will be added when needed

	return result
}

func agentDescriptionToMap(desc *protobufs.AgentDescription) map[string]interface{} {
	result := make(map[string]interface{})
	if len(desc.IdentifyingAttributes) > 0 {
		result["identifying_attributes"] = keyValueListToSlice(desc.IdentifyingAttributes)
	}
	if len(desc.NonIdentifyingAttributes) > 0 {
		result["non_identifying_attributes"] = keyValueListToSlice(desc.NonIdentifyingAttributes)
	}
	return result
}

func componentHealthToMap(health *protobufs.ComponentHealth) map[string]interface{} {
	result := make(map[string]interface{})
	result["healthy"] = health.Healthy
	if health.StartTimeUnixNano != 0 {
		result["start_time_unix_nano"] = health.StartTimeUnixNano
	}
	if health.LastError != "" {
		result["last_error"] = health.LastError
	}
	if health.Status != "" {
		result["status"] = health.Status
	}
	if health.StatusTimeUnixNano != 0 {
		result["status_time_unix_nano"] = health.StatusTimeUnixNano
	}
	return result
}

func effectiveConfigToMap(cfg *protobufs.EffectiveConfig) map[string]interface{} {
	result := make(map[string]interface{})
	if cfg.ConfigMap != nil {
		result["config_map"] = agentConfigMapToMap(cfg.ConfigMap)
	}
	return result
}

func agentConfigMapToMap(cfgMap *protobufs.AgentConfigMap) map[string]interface{} {
	result := make(map[string]interface{})
	if len(cfgMap.ConfigMap) > 0 {
		files := make(map[string]interface{})
		for k, v := range cfgMap.ConfigMap {
			files[k] = map[string]interface{}{
				"body":         v.Body,
				"content_type": v.ContentType,
			}
		}
		result["config_map"] = files
	}
	return result
}

func remoteConfigStatusToMap(status *protobufs.RemoteConfigStatus) map[string]interface{} {
	result := make(map[string]interface{})
	if len(status.LastRemoteConfigHash) > 0 {
		result["last_remote_config_hash"] = status.LastRemoteConfigHash
	}
	if status.Status != protobufs.RemoteConfigStatuses_RemoteConfigStatuses_UNSET {
		result["status"] = status.Status.String()
	}
	if status.ErrorMessage != "" {
		result["error_message"] = status.ErrorMessage
	}
	return result
}

func packageStatusesToMap(statuses *protobufs.PackageStatuses) map[string]interface{} {
	result := make(map[string]interface{})
	if len(statuses.Packages) > 0 {
		pkgs := make(map[string]interface{})
		for k, v := range statuses.Packages {
			pkgs[k] = packageStatusToMap(v)
		}
		result["packages"] = pkgs
	}
	if len(statuses.ServerProvidedAllPackagesHash) > 0 {
		result["server_provided_all_packages_hash"] = statuses.ServerProvidedAllPackagesHash
	}
	if statuses.ErrorMessage != "" {
		result["error_message"] = statuses.ErrorMessage
	}
	return result
}

func packageStatusToMap(status *protobufs.PackageStatus) map[string]interface{} {
	result := make(map[string]interface{})
	if status.Name != "" {
		result["name"] = status.Name
	}
	if status.AgentHasVersion != "" {
		result["agent_has_version"] = status.AgentHasVersion
	}
	if len(status.AgentHasHash) > 0 {
		result["agent_has_hash"] = status.AgentHasHash
	}
	if status.ServerOfferedVersion != "" {
		result["server_offered_version"] = status.ServerOfferedVersion
	}
	if len(status.ServerOfferedHash) > 0 {
		result["server_offered_hash"] = status.ServerOfferedHash
	}
	if status.Status != protobufs.PackageStatusEnum_PackageStatusEnum_Installed {
		result["status"] = status.Status.String()
	}
	if status.ErrorMessage != "" {
		result["error_message"] = status.ErrorMessage
	}
	return result
}

// AvailableComponents and ComponentDetails helpers removed - will be added when needed

func keyValueListToSlice(kvs []*protobufs.KeyValue) []map[string]interface{} {
	result := make([]map[string]interface{}, len(kvs))
	for i, kv := range kvs {
		result[i] = map[string]interface{}{
			"key":   kv.Key,
			"value": anyValueToInterface(kv.Value),
		}
	}
	return result
}

func anyValueToInterface(av *protobufs.AnyValue) interface{} {
	if av == nil {
		return nil
	}
	switch v := av.Value.(type) {
	case *protobufs.AnyValue_StringValue:
		return v.StringValue
	case *protobufs.AnyValue_BoolValue:
		return v.BoolValue
	case *protobufs.AnyValue_IntValue:
		return v.IntValue
	case *protobufs.AnyValue_DoubleValue:
		return v.DoubleValue
	case *protobufs.AnyValue_BytesValue:
		return v.BytesValue
	case *protobufs.AnyValue_ArrayValue:
		arr := make([]interface{}, len(v.ArrayValue.Values))
		for i, val := range v.ArrayValue.Values {
			arr[i] = anyValueToInterface(val)
		}
		return arr
	case *protobufs.AnyValue_KvlistValue:
		return keyValueListToSlice(v.KvlistValue.Values)
	default:
		return nil
	}
}

func mapToServerToAgent(data map[string]interface{}) (*protobufs.ServerToAgent, error) {
	msg := &protobufs.ServerToAgent{}

	// InstanceUid is string in Go protobuf (bytes in proto, but Go converts to string)
	if v, ok := data["instance_uid"].(string); ok {
		msg.InstanceUid = v
	} else if v, ok := data["instance_uid"].([]byte); ok {
		msg.InstanceUid = string(v)
	}

	if v, ok := data["capabilities"].(float64); ok {
		msg.Capabilities = uint64(v)
	}

	if v, ok := data["flags"].(float64); ok {
		msg.Flags = uint64(v)
	}

	// Remote config
	if v, ok := data["remote_config"].(map[string]interface{}); ok {
		remoteCfg, err := mapToAgentRemoteConfig(v)
		if err != nil {
			return nil, err
		}
		msg.RemoteConfig = remoteCfg
	}

	return msg, nil
}

func mapToAgentRemoteConfig(data map[string]interface{}) (*protobufs.AgentRemoteConfig, error) {
	cfg := &protobufs.AgentRemoteConfig{}

	if v, ok := data["config"].(map[string]interface{}); ok {
		configMap, err := mapToAgentConfigMap(v)
		if err != nil {
			return nil, err
		}
		cfg.Config = configMap
	}

	if v, ok := data["config_hash"].([]byte); ok {
		cfg.ConfigHash = v
	}

	return cfg, nil
}

func mapToAgentConfigMap(data map[string]interface{}) (*protobufs.AgentConfigMap, error) {
	cfgMap := &protobufs.AgentConfigMap{
		ConfigMap: make(map[string]*protobufs.AgentConfigFile),
	}

	if v, ok := data["config_map"].(map[string]interface{}); ok {
		for k, fileData := range v {
			if fileMap, ok := fileData.(map[string]interface{}); ok {
				file := &protobufs.AgentConfigFile{}
				if body, ok := fileMap["body"].([]byte); ok {
					file.Body = body
				}
				if ct, ok := fileMap["content_type"].(string); ok {
					file.ContentType = ct
				}
				cfgMap.ConfigMap[k] = file
			}
		}
	}

	return cfgMap, nil
}

func respondSuccess(message map[string]interface{}) {
	response := ParseResponse{
		Success: true,
		Message: message,
	}
	json.NewEncoder(os.Stdout).Encode(response)
}

func respondError(errMsg string) {
	response := ParseResponse{
		Success: false,
		Error:   errMsg,
	}
	json.NewEncoder(os.Stdout).Encode(response)
	os.Exit(1)
}

