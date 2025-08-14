#!/usr/bin/env python3
"""
Comprehensive test script for oivscode client
Tests multiple models with streaming and non-streaming responses
"""

import sys
import time
import traceback
from test_oivscode_client import oivscode

def test_model(client, model_name, test_streaming=True, test_non_streaming=True):
    """Test a specific model with both streaming and non-streaming responses"""
    results = {
        'model': model_name,
        'streaming': {'success': False, 'error': None, 'response_length': 0},
        'non_streaming': {'success': False, 'error': None, 'response_length': 0}
    }
    
    test_message = [{"role": "user", "content": "Hello! Please respond with exactly 3 sentences about AI."}]
    
    # Test non-streaming first
    if test_non_streaming:
        print(f"\n🔄 Testing {model_name} (non-streaming)...")
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=test_message,
                max_tokens=100,
                stream=False,
                timeout=30
            )
            
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                results['non_streaming']['success'] = True
                results['non_streaming']['response_length'] = len(content)
                print(f"✅ Non-streaming success: {content[:100]}{'...' if len(content) > 100 else ''}")
            else:
                results['non_streaming']['error'] = "No choices in response"
                print(f"❌ Non-streaming failed: No choices in response")
                
        except Exception as e:
            results['non_streaming']['error'] = str(e)
            print(f"❌ Non-streaming failed: {e}")
    
    # Test streaming
    if test_streaming:
        print(f"\n🔄 Testing {model_name} (streaming)...")
        try:
            stream = client.chat.completions.create(
                model=model_name,
                messages=test_message,
                max_tokens=100,
                stream=True,
                timeout=30
            )
            
            full_content = ""
            chunk_count = 0
            
            for chunk in stream:
                chunk_count += 1
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_content += delta.content
                        
                # Break after reasonable number of chunks to avoid infinite loops
                if chunk_count > 50:
                    break
            
            if full_content:
                results['streaming']['success'] = True
                results['streaming']['response_length'] = len(full_content)
                print(f"✅ Streaming success: {full_content[:100]}{'...' if len(full_content) > 100 else ''}")
                print(f"   📊 Received {chunk_count} chunks, {len(full_content)} characters")
            else:
                results['streaming']['error'] = "No content received in stream"
                print(f"❌ Streaming failed: No content received")
                
        except Exception as e:
            results['streaming']['error'] = str(e)
            print(f"❌ Streaming failed: {e}")
    
    return results

def main():
    """Main test function"""
    print("🚀 Starting comprehensive oivscode client test")
    print("=" * 60)
    
    # Initialize client
    try:
        client = oivscode(timeout=30)
        print(f"✅ Client initialized successfully")
        print(f"📍 Using endpoints: {client.api_endpoints}")
        print(f"🆔 User ID: {client.userid}")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Test a subset of models (avoid testing all to prevent rate limiting)
    test_models = [
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "gpt-4o-mini", 
        "claude-3-5-sonnet-20241022",
        "deepseek-v3",
        "grok-3-beta",
        "custom/blackbox-base"
    ]
    
    print(f"\n📋 Testing {len(test_models)} models:")
    for model in test_models:
        print(f"   • {model}")
    
    print("\n" + "=" * 60)
    
    # Test each model
    all_results = []
    
    for i, model in enumerate(test_models, 1):
        print(f"\n📊 Test {i}/{len(test_models)}: {model}")
        print("-" * 50)
        
        try:
            results = test_model(client, model)
            all_results.append(results)
            
            # Add delay between tests to be respectful to the API
            if i < len(test_models):
                print("⏱️  Waiting 2 seconds before next test...")
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error testing {model}: {e}")
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 TEST SUMMARY")
    print("=" * 60)
    
    streaming_success = 0
    non_streaming_success = 0
    total_tests = len(all_results)
    
    for result in all_results:
        model = result['model']
        streaming = result['streaming']
        non_streaming = result['non_streaming']
        
        print(f"\n🔍 {model}:")
        
        # Streaming results
        if streaming['success']:
            streaming_success += 1
            print(f"   ✅ Streaming: SUCCESS ({streaming['response_length']} chars)")
        else:
            print(f"   ❌ Streaming: FAILED - {streaming['error']}")
            
        # Non-streaming results  
        if non_streaming['success']:
            non_streaming_success += 1
            print(f"   ✅ Non-streaming: SUCCESS ({non_streaming['response_length']} chars)")
        else:
            print(f"   ❌ Non-streaming: FAILED - {non_streaming['error']}")
    
    print(f"\n🏆 FINAL RESULTS:")
    print(f"   📊 Total models tested: {total_tests}")
    print(f"   🌊 Streaming success: {streaming_success}/{total_tests} ({streaming_success/total_tests*100:.1f}%)")
    print(f"   📄 Non-streaming success: {non_streaming_success}/{total_tests} ({non_streaming_success/total_tests*100:.1f}%)")
    
    # Key findings
    print(f"\n🔑 KEY FINDINGS:")
    print(f"   🗝️  API Key Required: NO (using userid header instead)")
    print(f"   🔄 Endpoint Failover: YES (tries multiple endpoints)")
    print(f"   🌊 Streaming Support: {'YES' if streaming_success > 0 else 'NO'}")
    print(f"   📡 Network Access: {'YES' if streaming_success > 0 or non_streaming_success > 0 else 'NO'}")
    
    if streaming_success == 0 and non_streaming_success == 0:
        print(f"\n⚠️  WARNING: All tests failed. This could indicate:")
        print(f"   • Network connectivity issues")
        print(f"   • All endpoints are down")
        print(f"   • Missing dependencies")
        print(f"   • Rate limiting or blocking")

if __name__ == "__main__":
    main()