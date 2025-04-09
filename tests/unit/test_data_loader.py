"""
Unit tests for the data_loader module.
"""
import pytest
import os
import json
import pickle
from unittest.mock import patch, mock_open, MagicMock, call
import tempfile

# Import the functions to test
from data_loader import build_steam_data_index, load_summaries, get_game_data_by_appid

# Sample game data for testing
SAMPLE_GAME_DATA = [
    '{"appid": 123, "name": "Test Game 1", "genres": ["Action", "Adventure"]}',
    '{"appid": 456, "name": "Test Game 2", "genres": ["RPG", "Strategy"]}',
    '{"appid": 789, "name": "Test Game 3", "genres": ["Simulation", "Casual"]}'
]

# Sample summary data for testing
SAMPLE_SUMMARY_DATA = [
    '{"appid": 123, "summary": "This is a test summary for game 1"}',
    '{"appid": 456, "summary": "This is a test summary for game 2"}',
    '{"appid": 789, "summary": "This is a test summary for game 3"}'
]


def test_build_steam_data_index_new():
    """
    Test building a new index when no cache exists
    """
    # Create mock file data
    mock_file_data = '\n'.join(SAMPLE_GAME_DATA)
    
    # Mock pickle.dump to avoid serialization issues with MagicMock
    with patch('pickle.dump') as mock_dump:
        # Mock the open function for both the data file and cache file
        with patch('builtins.open', mock_open(read_data=mock_file_data)) as mock_file:
            # Mock os.path.exists to return False for cache file
            with patch('os.path.exists', return_value=False):
                # Call the function
                result = build_steam_data_index('fake_path.jsonl')
                
                # Verify the result has the expected keys
                assert 123 in result
                assert 456 in result
                assert 789 in result
                
                # Verify pickle.dump was called
                mock_dump.assert_called_once()


def test_build_steam_data_index_cached():
    """
    Test loading index from cache when it exists and is newer than the data file
    """
    # Create a mock index map
    mock_index_map = {123: 0, 456: 100, 789: 200}
    
    # Mock pickle.load to return our mock index map
    with patch('pickle.load', return_value=mock_index_map):
        # Mock os.path.exists to return True for cache file
        with patch('os.path.exists', return_value=True):
            # Mock os.path.getmtime to make cache file newer than data file
            with patch('os.path.getmtime', side_effect=[100, 200]):  # data_mtime, cache_mtime
                # Mock open to avoid actually opening any files
                with patch('builtins.open', mock_open()):
                    # Call the function
                    result = build_steam_data_index('fake_path.jsonl')
                    
                    # Verify the result is the same as our mock index map
                    assert result == mock_index_map


def test_build_steam_data_index_rebuild():
    """
    Test rebuilding index when cache exists but is older than the data file
    """
    # Create mock file data
    mock_file_data = '\n'.join(SAMPLE_GAME_DATA)
    
    # Mock pickle.dump to avoid serialization issues with MagicMock
    with patch('pickle.dump') as mock_dump:
        # Mock the open function for both the data file and cache file
        with patch('builtins.open', mock_open(read_data=mock_file_data)) as mock_file:
            # Mock os.path.exists to return True for cache file
            with patch('os.path.exists', return_value=True):
                # Mock os.path.getmtime to make data file newer than cache file
                with patch('os.path.getmtime', side_effect=[200, 100]):  # data_mtime, cache_mtime
                    # Call the function
                    result = build_steam_data_index('fake_path.jsonl')
                    
                    # Verify the result has the expected keys
                    assert 123 in result
                    assert 456 in result
                    assert 789 in result
                    
                    # Verify pickle.dump was called
                    mock_dump.assert_called_once()


def test_load_summaries():
    """
    Test loading summaries from a file
    """
    # Create mock file data
    mock_file_data = '\n'.join(SAMPLE_SUMMARY_DATA)
    
    # Mock os.path.exists to return True for summaries file
    with patch('os.path.exists', return_value=True):
        # Mock os.path.getsize to return a size
        with patch('os.path.getsize', return_value=1024):
            # Mock open to return our test data
            with patch('builtins.open', mock_open(read_data=mock_file_data)):
                # Call the function
                result = load_summaries('fake_summaries.jsonl')
                
                # Verify the result has the expected keys and values
                assert 123 in result
                assert 456 in result
                assert 789 in result
                assert result[123]['summary'] == 'This is a test summary for game 1'
                assert result[456]['summary'] == 'This is a test summary for game 2'
                assert result[789]['summary'] == 'This is a test summary for game 3'


def test_load_summaries_file_not_found():
    """
    Test loading summaries when the file does not exist
    """
    # Mock os.path.exists to return False
    with patch('os.path.exists', return_value=False):
        # Call the function
        result = load_summaries('nonexistent_file.jsonl')
        
        # Verify the result is an empty dictionary
        assert result == {}


def test_load_summaries_with_errors():
    """
    Test loading summaries with some invalid data
    """
    # Create mock file data with some invalid lines
    mock_file_data = (
        '{"appid": 123, "summary": "This is a test summary for game 1"}\n'
        'invalid json line\n'
        '{"appid": 456, "summary": "This is a test summary for game 2"}\n'
        '{"no_appid": true, "summary": "This has no appid field"}'
    )
    
    # Mock os.path.exists to return True for summaries file
    with patch('os.path.exists', return_value=True):
        # Mock os.path.getsize to return a size
        with patch('os.path.getsize', return_value=1024):
            # Mock open to return our test data
            with patch('builtins.open', mock_open(read_data=mock_file_data)):
                # Call the function
                result = load_summaries('fake_summaries.jsonl')
                
                # Verify only valid entries were loaded
                assert len(result) == 2
                assert 123 in result
                assert 456 in result


def test_get_game_data_by_appid():
    """
    Test retrieving game data using the index map
    """
    # Create mock index map and file data
    index_map = {123: 0, 456: len(SAMPLE_GAME_DATA[0]) + 1}  # +1 for newline
    
    # Create a proper mock for the file content
    mock_file_data = '\n'.join(SAMPLE_GAME_DATA)
    
    # Use the standard mock_open pattern but set up the handle to handle seeks correctly
    with patch('builtins.open', mock_open(read_data=mock_file_data)) as mock_file:
        # Get the mock file handle
        handle = mock_file.return_value
        
        # Set up seek method to track position
        original_seek = handle.seek
        position = [0]  # Use a list to store state between calls
        
        def mock_seek(new_pos, *args, **kwargs):
            position[0] = new_pos
            return original_seek(new_pos, *args, **kwargs)
        
        handle.seek = mock_seek
        
        # Set up readline to return different content based on position
        def mock_readline():
            if position[0] == 0:
                return SAMPLE_GAME_DATA[0]
            else:
                return SAMPLE_GAME_DATA[1]
        
        handle.readline.side_effect = mock_readline
        
        # Test first game (appid 123)
        result1 = get_game_data_by_appid(123, 'fake_path.jsonl', index_map)
        assert result1['appid'] == 123
        assert result1['name'] == 'Test Game 1'
        assert 'Action' in result1['genres']
        
        # Test second game (appid 456)
        result2 = get_game_data_by_appid(456, 'fake_path.jsonl', index_map)
        assert result2['appid'] == 456
        assert result2['name'] == 'Test Game 2'
        assert 'RPG' in result2['genres']


def test_get_game_data_by_appid_not_found():
    """
    Test retrieving game data for an appid not in the index map
    """
    # Create mock index map without the requested appid
    index_map = {123: 0, 456: 100}
    
    # Call the function with an appid not in the index
    result = get_game_data_by_appid(999, 'fake_path.jsonl', index_map)
    
    # Verify the result is None
    assert result is None


def test_get_game_data_by_appid_file_error():
    """
    Test retrieving game data when a file error occurs
    """
    # Create mock index map
    index_map = {123: 0}
    
    # Mock open to raise an exception
    with patch('builtins.open', side_effect=Exception("Test file error")):
        # Call the function
        result = get_game_data_by_appid(123, 'fake_path.jsonl', index_map)
        
        # Verify the result is None
        assert result is None


@pytest.mark.integration
def test_integration_data_loader():
    """
    Integration test using temporary files to test the full data loading process
    """
    # Skip this test if running in CI or if real files shouldn't be created
    if os.environ.get('SKIP_FILE_TESTS'):
        pytest.skip("Skipping tests that create real files")
    
    temp_dir = tempfile.mkdtemp()
    data_file_path = os.path.join(temp_dir, 'test_data.jsonl')
    summary_file_path = os.path.join(temp_dir, 'test_summaries.jsonl')
    cache_file_path = os.path.join(temp_dir, 'index_map.pkl')
    
    try:
        # Write test data to the files
        with open(data_file_path, 'w') as data_file:
            for line in SAMPLE_GAME_DATA:
                data_file.write(line + '\n')
        
        with open(summary_file_path, 'w') as summary_file:
            for line in SAMPLE_SUMMARY_DATA:
                summary_file.write(line + '\n')
        
        # Patch the cache file path
        with patch('data_loader.INDEX_CACHE_FILE', cache_file_path):
            # Build the index
            index_map = build_steam_data_index(data_file_path)
            
            # Verify the index contains all test appids
            assert 123 in index_map
            assert 456 in index_map
            assert 789 in index_map
            
            # Test loading a specific game
            game_data = get_game_data_by_appid(123, data_file_path, index_map)
            assert game_data['appid'] == 123
            assert game_data['name'] == 'Test Game 1'
            
            # Test loading summaries
            summaries = load_summaries(summary_file_path)
            assert 123 in summaries
            assert summaries[123]['summary'] == 'This is a test summary for game 1'
    
    finally:
        # Clean up the temporary files
        try:
            # Make sure all files are closed before unlinking
            os.unlink(data_file_path)
            os.unlink(summary_file_path)
            if os.path.exists(cache_file_path):
                os.unlink(cache_file_path)
            os.rmdir(temp_dir)
        except (IOError, OSError) as e:
            print(f"Error during cleanup: {e}")  # This will be printed in test output 