from utils import read_yaml, setup_logger
from config import CLASS_MAPPINGS, TARGET_CLASS_TO_ID

logger = setup_logger("mapper")

def get_class_mapping(dataset_alias, yaml_path):
    """
    Reads data.yaml of the given dataset, determines the original IDs,
    and returns a mapping dictionary {old_id: new_id or 'REMOVE'}.
    """
    logger.info(f"Generating class mapping for {dataset_alias} from {yaml_path}")
    data = read_yaml(yaml_path)
    original_names = data.get("names", [])
    
    if isinstance(original_names, dict):
        # Handle case where names might be a dictionary {id: name}
        original_names = [original_names[i] for i in range(len(original_names))]
        
    mapping_rules = CLASS_MAPPINGS.get(dataset_alias, {})
    
    id_mapping = {}
    for old_id, old_name in enumerate(original_names):
        if old_name in mapping_rules:
            target = mapping_rules[old_name]
            if target == "REMOVE":
                id_mapping[old_id] = "REMOVE"
            elif target in TARGET_CLASS_TO_ID:
                id_mapping[old_id] = TARGET_CLASS_TO_ID[target]
            else:
                logger.warning(f"Target class '{target}' not found in TARGET_CLASS_TO_ID.")
                id_mapping[old_id] = "REMOVE"
        else:
            logger.warning(f"No mapping rule found for class '{old_name}' in dataset '{dataset_alias}'. Marked for REMOVE.")
            id_mapping[old_id] = "REMOVE"
            
    logger.info(f"Mapping for {dataset_alias}: {id_mapping}")
    return id_mapping
