import os
from KNN_Classifier import Classifier
from utils import read_csv_in_directory
from config import paths
from logger import get_logger, log_error
from schema.data_schema import load_json_data_schema, save_schema
from preprocessing.pipeline import create_pipeline
from preprocessing.preprocess import handle_class_imbalance


logger = get_logger(task_name="train")


def run_training(
        input_schema_dir: str = paths.INPUT_SCHEMA_DIR,
        saved_schema_dir_path: str = paths.SAVED_SCHEMA_DIR_PATH,
        model_config_file_path: str = paths.MODEL_CONFIG_FILE_PATH,
        train_dir: str = paths.TRAIN_DIR,
        preprocessing_config_file_path: str = paths.PREPROCESSING_CONFIG_FILE_PATH,
        preprocessing_dir_path: str = paths.PREPROCESSING_DIR_PATH,
        predictor_dir_path: str = paths.PREDICTOR_DIR_PATH,
        default_hyperparameters_file_path: str = paths.DEFAULT_HYPERPARAMETERS_FILE_PATH,
        run_tuning: bool = False,
        hpt_specs_file_path: str = paths.HPT_CONFIG_FILE_PATH,
        hpt_results_dir_path: str = paths.HPT_OUTPUTS_DIR,
        explainer_config_file_path: str = paths.EXPLAINER_CONFIG_FILE_PATH,
        explainer_dir_path: str = paths.EXPLAINER_DIR_PATH,):
    try:
        logger.info("Starting training...")

        logger.info("Loading and saving schema...")
        data_schema = load_json_data_schema(input_schema_dir)
        save_schema(schema=data_schema, save_dir_path=saved_schema_dir_path)

        logger.info("Loading training data...")
        train_data = read_csv_in_directory(train_dir)
        features = data_schema.features
        target = data_schema.target
        x_train = train_data[features]
        y_train = train_data[target]
        pipeline = create_pipeline(data_schema)
        for stage, column in pipeline:
            if column is None:
                x_train = stage(x_train)
            elif column == 'schema':
                x_train = stage(x_train, data_schema)
            else:
                if stage.__name__ == 'remove_outliers_zscore':
                    x_train, y_train = stage(x_train, column, target=y_train)
                else:
                    x_train = stage(x_train, column)
        x_train, y_train = handle_class_imbalance(x_train, y_train)
        model = Classifier()
        model.fit(x_train, y_train)
        if not os.path.exists(predictor_dir_path):
            os.makedirs(predictor_dir_path)
        model.save(predictor_dir_path)
        logger.info('Model saved!')

    except Exception as exc:
        err_msg = "Error occurred during training."
        # Log the error
        logger.error(f"{err_msg} Error: {str(exc)}")
        # Log the error to the separate logging file
        log_error(message=err_msg, error=exc, error_fpath=paths.TRAIN_ERROR_FILE_PATH)
        # re-raise the error
        raise Exception(f"{err_msg} Error: {str(exc)}") from exc


if __name__ == "__main__":
    run_training()
