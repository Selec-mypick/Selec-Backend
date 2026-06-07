ROTATE_ACCESS_TOKEN_SCRIPT = """
local previous = redis.call('GET', KEYS[1])
if previous then
  redis.call('SET', KEYS[2], previous, 'EX', ARGV[3])
end
redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
return 1
"""
